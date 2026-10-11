import pytest

from fgsalary import config, data, model


@pytest.fixture(scope="session")
def parameters():
    return config.load_parameters()


@pytest.fixture(scope="session")
def skpg():
    return data.load_skpg()


@pytest.fixture(scope="session")
def sample(parameters, skpg):
    return data.simulate(parameters, skpg)


@pytest.fixture(scope="session")
def result(sample):
    return model.fit(sample)
