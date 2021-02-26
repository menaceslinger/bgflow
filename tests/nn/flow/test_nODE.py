import pytest
import torch
from bgtorch.distribution import NormalDistribution
from bgtorch.nn.flow import DiffEqFlow
from bgtorch.nn.flow.dynamics import BlackBoxDynamics, TimeIndependentDynamics
from bgtorch.nn.flow.estimator import BruteForceEstimator

dim = 1
n_samples = 100
prior = NormalDistribution(dim)
latent = prior.sample(n_samples)


class SimpleDynamics(torch.nn.Module):
    def __init__(self):
        super().__init__()

    def forward(self, xs):
        dxs = - 1 * xs
        return dxs


black_box_dynamics = BlackBoxDynamics(
    dynamics_function=TimeIndependentDynamics(SimpleDynamics()),
    divergence_estimator=BruteForceEstimator()
)

flow = DiffEqFlow(
    dynamics=black_box_dynamics
)


def test_nODE_flow_OTD():
    # Test forward pass of simple nODE with the OTD solver
    try:
        samples, dlogp = flow(latent)
    except ImportError:
        pytest.skip("Test requires torchdiffeq.")

    assert samples.std() < 1
    assert torch.allclose(dlogp, -torch.ones(n_samples))

    # Test backward pass of simple nODE with the OTD solver
    try:
        samples, dlogp = flow(latent, inverse=True)
    except ImportError:
        pytest.skip("Test requires torchdiffeq.")

    assert samples.std() > 1
    assert torch.allclose(dlogp, torch.ones(n_samples))


def test_nODE_flow_DTO():
    # Test forward pass of simple nODE with the DTO solver
    flow._use_checkpoints = True
    options = {
        "Nt": 20,
        "method": "RK4"
    }
    flow._kwargs = options

    try:
        samples, dlogp = flow(latent)
    except ImportError:
        pytest.skip("Test requires anode.")

    assert samples.std() < 1
    assert torch.allclose(dlogp, -torch.ones(n_samples))

    # Test backward pass of simple nODE with the DTO solver
    try:
        samples, dlogp = flow(latent, inverse=True)
    except ImportError:
        pytest.skip("Test requires torchdiffeq.")

    assert samples.std() > 1
    assert torch.allclose(dlogp, torch.ones(n_samples))
