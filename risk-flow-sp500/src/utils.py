import numpy as np
import pandas as pd


def is_positive_definite(matrix: np.ndarray) -> bool:
    try:
        np.linalg.cholesky(matrix)
        return True
    except np.linalg.LinAlgError:
        return False


def nearest_psd(matrix: np.ndarray) -> np.ndarray:
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    eigenvalues = np.clip(eigenvalues, 1e-8, None)
    return eigenvectors @ np.diag(eigenvalues) @ eigenvectors.T


def ledoit_wolf_shrinkage(
    covariance: np.ndarray, delta: float = 0.2
) -> np.ndarray:
    n = covariance.shape[0]
    avg_variance = np.mean(np.diag(covariance))
    target = avg_variance * np.eye(n)
    return (1 - delta) * covariance + delta * target


def compute_cholesky(covariance: np.ndarray) -> np.ndarray:
    if is_positive_definite(covariance):
        return np.linalg.cholesky(covariance)
    shrunk = ledoit_wolf_shrinkage(covariance)
    if is_positive_definite(shrunk):
        return np.linalg.cholesky(shrunk)
    psd = nearest_psd(shrunk)
    return np.linalg.cholesky(psd)


def verify_sdp(matrix: np.ndarray) -> tuple[bool, float]:
    eigenvalues = np.linalg.eigvalsh(matrix)
    min_eigenvalue = float(eigenvalues.min())
    return min_eigenvalue > 1e-10, min_eigenvalue
