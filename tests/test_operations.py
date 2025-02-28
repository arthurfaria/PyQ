import copy
from math import isclose
import random
import copy

import numpy as np
import networkx as nx
import torch
from torch.autograd import grad

random.seed(0)
np.random.seed(0)
torch.manual_seed(0)
torch.use_deterministic_algorithms(True)
from conftest import TestBatchedFM, TestFM, TestNetwork

from pyqtorch.ansatz import AlternateLayerAnsatz
from pyqtorch.core import operation

state_00 = torch.tensor([[1,0],[0,0]], dtype=torch.cdouble).unsqueeze(2)
state_10 = torch.tensor([[0,1],[0,0]], dtype=torch.cdouble).unsqueeze(2)
state_01 = torch.tensor([[0,0],[1,0]], dtype=torch.cdouble).unsqueeze(2)
state_11 = torch.tensor([[0,0],[0,1]], dtype=torch.cdouble).unsqueeze(2)

pi = torch.tensor(torch.pi, dtype=torch.cdouble)

CNOT_mat: torch.Tensor = torch.tensor(
        [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]], dtype=torch.cdouble)


# TODO: these are all the same test, would be better to parameterize a test
def test_batched_network() -> None:
    ansatz = AlternateLayerAnsatz(n_qubits=4, n_layers=4)
    network = TestNetwork([TestFM(), ansatz])
    batched_network = TestNetwork([TestBatchedFM(), ansatz])
    # to ensure the parameters are the same
    batch_size = 2
    x = torch.linspace(-0.5, 0.5, batch_size).reshape(batch_size, 1).requires_grad_()
    bx = torch.linspace(-0.5, 0.5, batch_size).reshape(batch_size, 1).requires_grad_()
    y0: torch.Tensor = network(x[0])
    y1: torch.Tensor = network(x[1])
    by: torch.Tensor = batched_network(bx)

    gby = grad(by, bx, torch.ones_like(by), create_graph=True)
    gy0 = grad(y0, x, torch.ones_like(y0), create_graph=True)
    gy1 = grad(y1, x, torch.ones_like(y1), create_graph=True)

    assert torch.allclose(by[0], y0)
    assert torch.allclose(by[1], y1)
    assert torch.allclose(gby[0][0], gy0[0][0])
    assert torch.allclose(gby[0][1], gy1[0][1])


def test_batched_fm() -> None:
    network = TestNetwork([TestFM()])
    batched_network = TestNetwork([TestBatchedFM()])

    batch_size = 3
    x = torch.linspace(-0.5, 0.5, batch_size).reshape(batch_size, 1).requires_grad_()
    bx = torch.linspace(-0.5, 0.5, batch_size).reshape(batch_size, 1).requires_grad_()

    y0: torch.Tensor = network(x[0])
    y1: torch.Tensor = network(x[1])
    by: torch.Tensor = batched_network(bx)

    gby = grad(by, bx, torch.ones_like(by), create_graph=True)
    gy0 = grad(y0, x, torch.ones_like(y0), create_graph=True)
    gy1 = grad(y1, x, torch.ones_like(y1), create_graph=True)

    # Assert result values are the same for single layer
    assert torch.allclose(by[0], y0)
    assert torch.allclose(by[1], y1)
    # Assert gradients are the same
    assert torch.allclose(gby[0][0], gy0[0][0])
    assert torch.allclose(gby[0][1], gy1[0][1])


def test_batched_ansatz() -> None:
    network = TestNetwork(
        network=[AlternateLayerAnsatz(n_qubits=2, n_layers=1)], n_qubits=2
    )

    batch_size = 2
    x = torch.linspace(-0.5, 0.5, batch_size).reshape(batch_size, 1).requires_grad_()
    bx = torch.linspace(-0.5, 0.5, batch_size).reshape(batch_size, 1).requires_grad_()
    y0: torch.Tensor = network(x[0])
    y1: torch.Tensor = network(x[1])
    by: torch.Tensor = network(bx)

    assert torch.allclose(by[0], y0)
    assert torch.allclose(by[1], y1)


def test_CNOT_state00_controlqubit_0() -> None:
    result: torch.Tensor = operation.CNOT(state_00, (0,1), 2)
    assert torch.equal(state_00, result)


def test_CNOT_state10_controlqubit_0() -> None:
    result: torch.Tensor = operation.CNOT(state_10, (0,1), 2)
    assert torch.equal(state_11, result)


def test_CNOT_state11_controlqubit_0() -> None:
    result: torch.Tensor = operation.CNOT(state_11, (0,1), 2)
    assert torch.equal(state_10, result)


def test_CNOT_state00_controlqubit_1() -> None:
    result: torch.Tensor = operation.CNOT(state_00, (1,0), 2)
    assert torch.equal(state_00, result)


def test_CNOT_state10_controlqubit_1() -> None:
    result: torch.Tensor = operation.CNOT(state_10, (1,0), 2)
    assert torch.equal(state_10, result)


def test_CNOT_state11_controlqubit_1() -> None:
    result: torch.Tensor = operation.CNOT(state_11, (1,0), 2)
    assert torch.equal(state_01, result)


def test_CRY_state10_controlqubit_0() -> None:
    result: torch.Tensor = operation.CRY(pi, state_10, (0,1), 2)
    assert torch.allclose(state_11, result)


def test_CRY_state01_controlqubit_0() -> None:
    result: torch.Tensor = operation.CRY(pi, state_01, (1,0), 2)
    assert torch.allclose(state_11, result)