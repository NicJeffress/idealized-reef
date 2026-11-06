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
#undef  SPLINES_VVISC  /* off: BSTRESS_IMPLICIT and VEG_DRAG_IMPLICIT need the tridiagonal viscous solve (since 2026-11-02) */

#undef TS_FIXED   /* Reef_Ideal_A15_veg_strat: temperature and salinity evolve */

/* Open north boundary options for stratified runs, all switched at run
   time in ocean.in (default: nudged radiation plus the interior nudging
   band, sponge off; see the case README):
   - nudged radiation: LBC(isUvel/isVvel/isTvar) north = RadNud, exterior
     state = the initial stratification at rest
   - interior nudging band: Lm3CLM, LtracerCLM, LnudgeM3CLM, LnudgeTCLM = T,
     band USER(3) m wide, time scale USER(4) h at the boundary
   - viscous/diffusive sponge: LuvSponge, LtracerSponge = T, USER(5) m2/s */
#define ANA_TOBC      /* RadNud tracers: initial state (case ana_tobc.h) */
#define ANA_M3OBC     /* RadNud 3-D velocity: rest (ROMS default) */
#define ANA_TCLIMA    /* nudging band: initial tracers (case ana_tclima.h) */
#define ANA_M3CLIMA   /* nudging band: rest (case ana_m3clima.h) */
#define ANA_NUDGCOEF  /* nudging band width/time (case ana_nudgcoef.h) */
#define ANA_SPONGE    /* viscous band (case ana_sponge.h; not the grid file's) */
#define TS_DIF2       /* horizontal tracer diffusion: sponge band only (TNU2 = 0) */
#define MIX_GEO_TS    /* ... along geopotentials */

#define SOLVE3D
#undef  WEC_MELLOR
#define WEC_VF
#define STOKES_INTERVAL /* spectral Stokes drift updated STOKES_NCPL times per wave exchange (coawst-cloud roms-stokes-interval); A15 default since 2026-11-06 */
#define WDISS_WAVEMOD
#define ROLLER_RENIERS  /* Reniers surface roller, WEC_ALPHA 0.5 in ocean.in; A15 default since 2026-11-03
                         (user); needs coawst-cloud roms-roller-substeps (DT 6 s) and roms-restart-roller
                         (restarts); notebook 2026-11-03_roller-checks */
#define TKE_WAVEDISS  /* surface TKE flux from SWAN's breaking dissipation (SZ_ALPHA); A15 default since
                         2026-11-03 (user): with triads the fore-reef flow is less surface-intensified
                         (-32 %), as the physics expects (notebook 2026-11-03_density1-canopy-tests) */
#define ZOS_HSIG      /* surface roughness from the wave height (ZOS_HSIG_ALPHA), with TKE_WAVEDISS */
#define UV_KIRBY
#define BOTTOM_STREAMING  /* wave momentum lost to bottom friction -> mean flow (WEC_VF); A15 default
                           since 2026-11-03 (author): set-up +57 %; notebook 2026-11-03_wave-streaming */

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
#define VEGETATION      /* canopy (frontal area) drag; plant fields from init_reef.nc */
# ifdef VEGETATION
#  undef ANA_VEGETATION
#  define VEG_DRAG
#  ifdef VEG_DRAG
#   define VEG_DRAG_IMPLICIT  /* canopy drag backward Euler (coawst-cloud 3-experimental/roms-veg-implicit);
                                 default since 2026-11-02 (user): with triads acting the explicit drag
                                 blows up at DT 6 s even on the constant canopy */
#   undef VEG_FLEX
#   define VEG_TURB
#  endif
#  define VEG_SWAN_COUPLING  /* ROMS sends plant density/height/diameter to SWAN */
#  define VEG_STREAMING  /* wave momentum lost to the canopy -> mean flow in the canopy layers; A15 default
                           since 2026-11-03 (author), with BOTTOM_STREAMING set-up +95 %; needs
                           coawst-cloud roms-veg-streaming-fixes (4abff12 on) */
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
