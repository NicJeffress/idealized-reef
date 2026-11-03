/*
** svn $Id: inlet_test.h 838 2008-11-17 04:22:18Z jcwarner $
*******************************************************************************
** Copyright (c) 2002-2008 The ROMS/TOMS Group                               **
**   Licensed under a MIT/X style license                                    **
**   See License_ROMS.txt                                                    **
*******************************************************************************
**
** Options for Reef Toy Case, waves-ocean (SWAN/ROMS) two-way coupling.
**
** Application flag:   REEF_IDEAL_A15
** Input script:       ocean.in
**                     coupling.in
*/

#define ROMS_MODEL
#define SWAN_MODEL
#define MCT_LIB
#undef MCT_INTERP_OC2WV
#define SALINITY
#define PERFECT_RESTART

#undef WET_DRY
#undef CURVGRID
#define VISC_GRID

#define UV_VIS2
#define MIX_S_UV
#define MASKING
#define UV_ADV
#define UV_COR
#define DJ_GRADPS
#define STEP2D_FB_AB3_AM4 /* AB3-AM4 barotropic kernel (coawst-cloud 3-experimental/roms-step2d-fb);
                             A15 default since 2026-11-02 (user): within the bare-reef noise floor
                             and 19 % faster than LF-AM3 (notebook 2026-11-02_options-triads-on) */
#define SPLINES_VDIFF
#undef  SPLINES_VVISC  /* off: BSTRESS_IMPLICIT needs the tridiagonal viscous solve (since 2026-11-02) */

#define TS_FIXED

#define SOLVE3D
#undef  WEC_MELLOR
#define WEC_VF
#define WDISS_WAVEMOD
#define TKE_WAVEDISS  /* surface TKE flux from SWAN's breaking dissipation (SZ_ALPHA); A15 default since
                         2026-11-03 (user): with triads the fore-reef flow is less surface-intensified
                         (-32 %), as the physics expects (notebook 2026-11-03_density1-canopy-tests) */
#define ZOS_HSIG      /* surface roughness from the wave height (ZOS_HSIG_ALPHA), with TKE_WAVEDISS */
#define UV_KIRBY
#undef BOTTOM_STREAMING

#undef ANA_INITIAL
#define ANA_SMFLUX
#define ANA_FSOBC
#define ANA_M2OBC

#undef ANA_PAIR
#undef ATM_PRESS

/* define only one of the following 5 */
#undef UV_LOGDRAG
#undef  UV_QDRAG
#undef  MB_BBL
#undef  SG_BBL
#define SSW_BBL
#define BSTRESS_IMPLICIT  /* bottom stress backward Euler (coawst-cloud 3-experimental/roms-bstress-implicit;
                             needs SPLINES_VVISC off); A15 default since 2026-11-02 (user): equals the
                             uncapped explicit stress within 0-3 %, stable without LIMIT_BSTRESS's cap */
#ifdef SSW_BBL
#define SSW_CALC_ZNOT
#define SSW_LOGINT
/* define one of these 2 */
#define SSW_LOGINT_WBL
#undef  SSW_LOGINT_DIRECT
#endif

/*#undef SEDIMENT
#undef ANA_SEDIMENT*/

/* Vegetation flags*/
#undef VEGETATION
# ifdef VEGETATION
#  undef ANA_VEGETATION
#  define VEG_DRAG
#  ifdef VEG_DRAG
#   undef VEG_FLEX
#   define VEG_TURB
#  endif
#  undef VEG_SWAN_COUPLING
#  undef VEG_STREAMING
# endif

#ifdef SOLVE3D
# define GLS_MIXING
# ifdef GLS_MIXING
#  define RI_SPLINES
#  define KANTHA_CLAYSON
#  define N2S2_HORAVG
#   ifdef VEG_TURB
#    undef N2S2_HORAVG
#   endif
# endif

# define ANA_STFLUX
# define ANA_SSFLUX
# define ANA_BPFLUX
# define ANA_BTFLUX
# define ANA_BSFLUX
# define ANA_SPFLUX
# define ANA_SRFLUX
#endif

#undef FLOATS
#define AVERAGES
# undef STATIONS
#define DIAGNOSTICS_UV
