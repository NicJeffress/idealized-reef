"""Barotropic Courant-number limit of ROMS's AB3-AM4 kernel (STEP2D_FB_AB3_AM4).

Usage: python3 -I tools/fb_stability.py

Von Neumann analysis of the generalized forward-backward AB3-AM4 step
(step2d_FB.h, Shchepetkin & McWilliams 2005, Sec. 2.3) for linear shallow
water on the C-grid with constant depth:

  zeta(m+1) = zeta(m) - dt H div(f0 u(m) + f1 u(m-1) + f2 u(m-2))
  u(m+1)    = u(m) - dt g grad(b_new zeta(m+1) + b0 zeta(m) + b1 zeta(m-1)
                               + b2 zeta(m-2))

For a Fourier mode both operators become i a with a = sqrt(gH) dt k_eff; the
grid's worst mode has k_eff = 2 sqrt(1/dx^2 + 1/dy^2), so the Courant number
of tools/cfl_check.py, C = sqrt(gH) dt sqrt(1/dx^2 + 1/dy^2), is a/2. Prints
the largest stable a (the paper's alpha_max) and C. Real limits are somewhat
lower (varying depth, nonlinear terms); Shchepetkin quotes about 0.87.
"""
import numpy as np

FWD = (1.781105, -1.06221, 0.281105)          # f0, f1, f2 (step2d_FB.h)
BKW = (0.614, 0.285, 0.0880, 0.013)           # b_new, b0, b1, b2


def amplification(a):
    f0, f1, f2 = FWD
    bn, b0, b1, b2 = BKW
    # state (zeta_m, zeta_m-1, zeta_m-2, u_m, u_m-1, u_m-2), g = H = 1
    zrow = np.array([1, 0, 0, -1j * a * f0, -1j * a * f1, -1j * a * f2])
    urow = np.array([0, 0, 0, 1, 0, 0], complex) - 1j * a * (bn * zrow + np.array([b0, b1, b2, 0, 0, 0]))
    m = np.zeros((6, 6), complex)
    m[0], m[3] = zrow, urow
    m[1, 0] = m[2, 1] = m[4, 3] = m[5, 4] = 1
    return max(abs(np.linalg.eigvals(m)))


def main():
    a = 0.0
    while amplification(a + 1e-4) <= 1 + 1e-9:
        a += 1e-4
    print(f"AB3-AM4: alpha_max = {a:.3f}, barotropic Courant limit C = {a / 2:.3f}")


if __name__ == "__main__":
    main()
