%% Intro
%makes a very simple init file
clear all
%% Paths
init_file='init_reef.nc';
grid_file='roms_grid_default_1.nc';  %<-enter name of grid here
swan_grid_file = 'Reef_grid_swan_default_1.mat';
%% Values to Change

init_time = 0;
theta_s = 3.0;
theta_b = 2.0;
Tcline = 20;
Vtransform = 2;
Vstretching = 4;
N = 10;
zeta_value = 0;
u_value = 0;
ubar_value = 0;
v_value = 0;
vbar_value = 0;
salt_value = 35;
temp_value = 18;
NAT = 2;    %Number of active tracers. Usually 2 (temp + salt).

%one needs sediment (NCS or NNS or both) if you use SSW_BBL or any other BBL

%NCS and NNS should be the same as in mod_param.F
NCS = 0;   %number of cohesive sed classes (mud sediments)
NNS = 0;   %number of non-cohesive sed classes (sand sediments)
Nbed = 0;   %number of bed layers, should be the same as in mod_param.F

NVEG=1; %number of vegetation types

if (NVEG>0)
% plant_density_val=2500;
% plant_height_val=0.3;
% plant_diameter_val=0.01;
% plant_thickness_val=0.01;

plant_density_val=0.001;
plant_height_val=0.001;
plant_diameter_val=0.001;
plant_thickness_val=0.001;

end
zob_val=0.01;
kn_val=zob_val*30;
grain_diameter_val=kn_val./2.5;
grain_density_val=2650;
settling_vel_val=0.15;
erosion_stress_val=0.2;

%% Dont change Below

%works for NCS,NNS,Nbed=0


%% Grid, zeta, u,ubar,v,vbar,salt,temp
% grid stuff
h=ncread(grid_file,'h');
hmin=min(h(:));
hc=min([hmin,Tcline]);

hc=Tcline;%changed to what Taran is using

[LP,MP]=size(h);
L  = LP-1;
M  = MP-1;
xi_psi  = L;
xi_rho  = LP;
xi_u    = L;
xi_v    = LP;
eta_psi = M;
eta_rho = MP;
eta_u   = MP;
eta_v   = M;
%
% These are just copied from above, and then we call get_roms_grid.
%
Sinp.N           =N;            %number of vertical levels
Sinp.Vtransform  =Vtransform;   %vertical transformation equation
Sinp.Vstretching =Vstretching;  %vertical stretching function
Sinp.theta_s     =theta_s;      %surface control parameter
Sinp.theta_b     =theta_b;      %bottom  control parameter
Sinp.Tcline      =Tcline;       %surface/bottom stretching width
Sinp.hc          =hc;           %stretching width used in ROMS
%

Gout=get_roms_grid(grid_file,Sinp);

%zeta
zeta(1:xi_rho,1:eta_rho,1:length(init_time)) = zeta_value;

%u and ubar
u(1:xi_u,1:eta_u,1:N,1:length(init_time)) = u_value;
ubar(1:xi_u,1:eta_u,1:length(init_time)) = ubar_value;

%v and vbar
v(1:xi_v,1:eta_v,1:N,1:length(init_time)) = v_value;
vbar(1:xi_v,1:eta_v,1:length(init_time)) = vbar_value;

%salt and temp
salt(1:xi_rho,1:eta_rho,1:N,1:length(init_time)) = salt_value;
temp(1:xi_rho,1:eta_rho,1:N,1:length(init_time)) = temp_value;

%% Veg
if (NVEG>0)
plant_density(1:xi_rho,1:eta_rho,1:NVEG)=plant_density_val;
plant_height(1:xi_rho,1:eta_rho,1:NVEG)=plant_height_val;
plant_diameter(1:xi_rho,1:eta_rho,1:NVEG)=plant_diameter_val;
plant_thickness(1:xi_rho,1:eta_rho,1:NVEG)=plant_thickness_val;
marsh_mask=zeros(xi_rho,eta_rho,NVEG);

%these 2 are for a quick test NJ 11/20
grain_diameter(1:xi_rho,1:eta_rho,NVEG)=grain_diameter_val;
grain_density(1:xi_rho,1:eta_rho,NVEG)=grain_density_val;
settling_vel(1:xi_rho,1:eta_rho,NVEG)=settling_vel_val;
erosion_stress(1:xi_rho,1:eta_rho,NVEG)=erosion_stress_val;
end

%% Sediment
% calc sed parameters. Do not alter.
%
NST = NCS + NNS;     % total number of sed tracers.
NT = NAT+NST;        % total number of tracers.

%% Now actually write to netcdf

create_roms_netcdf_init_mw(init_file,Gout,Nbed,NNS,NCS,NVEG)
%create_roms_netcdf_init_mw_local(init_file,Gout,Nbed,NNS,NCS,NVEG)

%now write the data from the arrays to the netcdf file
disp(' ## Filling Variables in netcdf file with data...')

ncwrite(init_file,'theta_s',Gout.theta_s);
ncwrite(init_file,'theta_b',Gout.theta_b);
ncwrite(init_file,'Tcline',Gout.Tcline);
ncwrite(init_file,'Cs_r',Gout.Cs_r);
ncwrite(init_file,'Cs_w',Gout.Cs_w);
ncwrite(init_file,'sc_w',Gout.s_w);%s_w
ncwrite(init_file,'sc_r',Gout.s_rho);
ncwrite(init_file,'hc',Gout.hc);
ncwrite(init_file,'Vtransform',Gout.Vtransform);
ncwrite(init_file,'Vstretching',Gout.Vstretching);
ncwrite(init_file,'spherical',Gout.spherical);

ncwrite(init_file,'ocean_time',init_time);

ncwrite(init_file,'zeta',zeta);
ncwrite(init_file,'ubar',ubar);
ncwrite(init_file,'vbar',vbar);
ncwrite(init_file,'u',u);
ncwrite(init_file,'v',v);
ncwrite(init_file,'temp',temp);
ncwrite(init_file,'salt',salt);


if (NVEG>0)
ncwrite(init_file,'plant_height',plant_height);
ncwrite(init_file,'plant_diameter',plant_diameter);
ncwrite(init_file,'plant_density',plant_density);
ncwrite(init_file,'plant_thickness',plant_thickness);
ncwrite(init_file,'marsh_mask',marsh_mask);

ncwrite(init_file,'grain_diameter',grain_diameter);
ncwrite(init_file,'grain_density',grain_density);
ncwrite(init_file,'settling_vel',settling_vel);
ncwrite(init_file,'erosion_stress',erosion_stress);
end

%close file
disp(['created ', init_file])



%% Send info over to swan to make swan grids

swan=load(swan_grid_file);

% if (NVEG>0)
% roms2swan_NJ(grid_file,init_file);
% else
%     roms2swan_NJ(grid_file,[]);
% end
% disp('Made the swan files')

[xi_rho_swan,eta_rho_swan]=size(swan.hswan);

if (NVEG>0)
plant_density_swan(1:xi_rho_swan,1:eta_rho_swan,1:NVEG)=plant_density_val;
plant_height_swan(1:xi_rho_swan,1:eta_rho_swan,1:NVEG)=plant_height_val;
plant_diameter_swan(1:xi_rho_swan,1:eta_rho_swan,1:NVEG)=plant_diameter_val;
plant_thickness_swan(1:xi_rho_swan,1:eta_rho_swan,1:NVEG)=plant_thickness_val;
marsh_mask_swan=zeros(xi_rho_swan,eta_rho_swan,NVEG);
end

%write_swan_plants_NJ(h,npla,npla_hght,npla_diam,npla_thck)

write_swan_plants_NJ(swan.hswan , plant_density_swan , plant_height_swan,...
    plant_diameter_swan , plant_thickness_swan);

%% Subfunctions
function Gout = get_roms_grid(Ginp, Sinp, Tindex)

%
% GET_ROMS_GRID:  Builds or updates ROMS grid structure
%
% Gout = get_roms_grid(Ginp)
% Gout = get_roms_grid(Ginp, Sinp)
% Gout = get_roms_grid(Ginp, Sinp, Tindex)
% Gout = get_roms_grid(Ginp, Tindex)
%
% This function builds or updates a ROMS Grid structure (Gout) containing
% all the variables associated with the application's horizontal and
% vertical grids.
%
% On Input:
%
%    Ginp          ROMS Grid/History NetCDF file/URL name containing
%                    all grid variables (string)
%
%              or, an existing grid structure to which the vertical
%                    coordinates are added or updated (struct array)
%
%    Sinp          ROMS output NetCDF file/URL name from which the
%                    vertical coordinates can be determined (string)
%
%              or, a structure containing vertical coordinates
%                    stretching parameters (struct array):
%
%                    Sinp.N               number of vertical levels
%                    Sinp.Vtransform      vertical transformation equation
%                    Sinp.Vstretching     vertical stretching function
%                    Sinp.theta_s         surface control parameter
%                    Sinp.theta_b         bottom  control parameter
%                    Sinp.Tcline          surface/bottom stretching width
%                    Sinp.hc              stretching width used in ROMS
%
%    Tindex        Time record index used to process free-surface in the
%                    vertical coordinates (OPTIONAL, scalar):
%
%                    If Tindex is omitted, zero or empty, it assumes
%                      that zeta=0 yielding unperturbed depths
%
%                    Otherwise, the free-surface record in input NetCDF
%                      is processed.  The free-surface is read from
%                      either Ginp (if history file) or Sinp (if provided
%                      and history file).
%
% On Output:
%
%    Gout          ROMS grid variables structure (struct array)
%
% Examples:
%
%    Gout = get_roms_grid('ocean_grd.nc');
%
%           will return a structure of all grid variables except all
%           those associated with the vertical grid. The vertical
%           coordinate parameters and free-surface are not present.
%
%    Gout = get_roms_grid('ocean_grd.nc', 'ocean_his.nc');
%
%           will return a structure of all grid variables. The vertical
%           depths are unperturbed (zeta=0) since the time record to
%           process was not specified.
%
%    Gout = get_roms_grid('ocean_grd.nc', 'ocean_his.nc', MyTimeRec);
%
%           will return a structure of all grid variables. The vertical
%           depths are time dependent because time record to process
%           was specified.
%
%    Gout = get_roms_grid('ocean_his.nc', MyTimeRec);
%
%           will return a structure of all grid variables. I assumes that
%           the ROMS history file 'ocean_his.nc' contains all the grid
%           variables. That is, NO_WRITE_GRID option was not activated.
%

% svn $Id: get_roms_grid.m 996 2020-01-10 04:28:56Z arango $
%=========================================================================%
%  Copyright (c) 2002-2020 The ROMS/TOMS Group                            %
%    Licensed under a MIT/X style license                                 %
%    See License_ROMS.txt                           Hernan G. Arango      %
%=========================================================================%

% Check input arguments.
  
process.horizontal = false;
process.parameters = false;
process.zeta       = false;
process.vertical   = false;

TimeRecord = [];

if (~isstruct(Ginp))
  Gout.grid_name    = Ginp;

  Ginfo = nc_inq(Ginp);
  vnames = {Ginfo.Variables.Name};           % Available variables
  anames = {Ginfo.Attributes.Name};          % Available global attributes
  NvarsG = length(Ginfo.Variables);          % Number of variables
end
if (nargin > 1)
  if (ischar(Sinp))
    process.zeta = true;
    Gout.his_name = Sinp;                    % Sinp is a NetCDF file
  elseif (isstruct(Sinp))
    process.parameters = true;               % Sinp are vertical parameters
  elseif (isnumeric(Sinp) && nargin == 2)
    process.zeta = true;
    TimeRecord = Sinp;                       % Sinp is time record index
  end
end
if (nargin == 3)
  TimeRecord = Tindex;
end

% Initialize.

spherical = false;

if (~isstruct(Ginp))
  if (any(strcmp(anames,'coarse_factor')) ||                            ...
      any(strcmp(anames,'refine_factor')))
    index = strcmp(anames,'parent_grid');
    if (any(index))
      Gout.parent_grid = Ginfo.Attributes(index).Value;
    end
  end
  Gout.TimeRecord    = TimeRecord;
  Gout.Lm            = [];
  Gout.Mm            = [];
  Gout.N             = [];
  Gout.coarse_factor = 0;
  if (any(strcmp(anames,'coarse_factor')))
    Gout.parent_Imin = [];
    Gout.parent_Imax = [];
    Gout.parent_Jmin = [];
    Gout.parent_Jmax = [];
  end
  Gout.refine_factor = 0;
  Gout.coarse_factor = [];
  if (any(strcmp(anames,'refine_factor')))
    Gout.parent_Imin = [];
    Gout.parent_Imax = [];
    Gout.parent_Jmin = [];
    Gout.parent_Jmax = [];
  end
  Gout.Vtransform    = [];
  Gout.Vstretching   = [];
  Gout.theta_s       = [];
  Gout.theta_b       = [];
  Gout.Tcline        = [];
  Gout.hc            = [];
  Gout.s_rho         = [];
  Gout.Cs_r          = [];
  Gout.s_w           = [];
  Gout.Cs_w          = [];

  spherical = nc_read(Ginp,'spherical');
  
  if (ischar(spherical))
    if (spherical == 'T' || spherical == 't')
      spherical = 1;
    else
      spherical = 0;
    end
  end
  Gout.spherical = spherical;
  Gout.uniform = false;
  Gout.curvilinear = false;
  Gout.vector_rotation = false;
else
  if (~isempty(Ginp.spherical))
    spherical = Ginp.spherical;
  end
end

%--------------------------------------------------------------------------
% Set variable list to process and switches.
%--------------------------------------------------------------------------

varhor  = {'x_rho', 'y_rho', 'x_psi', 'y_psi',                          ...
           'x_u', 'y_u',  'x_v', 'y_v'};
if (~spherical)
  varhor = [varhor, 'x_perimeter', 'y_perimeter',                       ...
                    'x_rho_west',  'y_rho_west',                        ...
                    'x_rho_east',  'y_rho_east',                        ...
                    'x_rho_south', 'y_rho_south',                       ...
                    'x_rho_north', 'y_rho_north',                       ...
                    'x_u_west',    'y_u_west',                          ...
                    'x_u_east',    'y_u_east',                          ...
                    'x_u_south',   'y_u_south',                         ...
                    'x_u_north',   'y_u_north',                         ...
                    'x_v_west',    'y_v_west',                          ...
                    'x_v_east',    'y_v_east',                          ...
                    'x_v_south',   'y_v_south',                         ...
                    'x_v_north',   'y_v_north'];
else
  varhor = [varhor, 'lon_rho', 'lat_rho', 'lon_psi', 'lat_psi',         ...
                    'lon_u', 'lat_u', 'lon_v', 'lat_v',                 ...
                    'lon_perimeter', 'lat_perimeter',                   ...
	            'lon_rho_west',  'lat_rho_west',                    ...
                    'lon_rho_east',  'lat_rho_east',                    ...
                    'lon_rho_south', 'lat_rho_south',                   ...
                    'lon_rho_north', 'lat_rho_north',                   ...
                    'lon_u_west',    'lat_u_west',                      ...
                    'lon_u_east',    'lat_u_east',                      ...
                    'lon_u_south',   'lat_u_south',                     ...
                    'lon_u_north',   'lat_u_north',                     ...
                    'lon_v_west',    'lat_v_west',                      ...
                    'lon_v_east',    'lat_v_east',                      ...
                    'lon_v_south',   'lat_v_south',                     ...
                    'lon_v_north',   'lat_v_north'];
end
varhor  = [varhor, 'mask_rho', 'mask_psi', 'mask_u', 'mask_v',          ...
                   'angle', 'pm', 'pn', 'dndx', 'dmde', 'h', 'f'];
varver  = {'Vtransform', 'Vstretching',                                 ...
           'theta_s', 'theta_b', 'Tcline', 'hc',                        ...
           's_rho', 'Cs_r', 's_w', 'Cs_w',                              ...
           'Hz', 'z_rho', 'z_u', 'z_v'};
varlist = [varhor, varver];

if (isstruct(Ginp))

  Gout = Ginp;
  
  got.N    = false;
  got.zeta = false;

  for var = varlist
    field = char(var);
    got.(field) = false;
    if (isfield(Gout,field))
      got.(field) = true;
    end
  end

else

  process.horizontal = true;

  got.N              = false;
  got.zeta           = false;
  got.lon_coast      = any(strcmp(vnames,'lon_coast'));
  got.lat_coast      = any(strcmp(vnames,'lat_coast'));

  for var = varlist
    field = char(var);
    got.(field) = false;
  end
   
  for n = 1:NvarsG
    field = char(Ginfo.Variables(n).Name);
    if (isfield(got,field))
      got.(field) = true;
    end

% If "Ginp" is a ROMS output NetCDF file, read in vertical coordinate
% parameters.

    switch field  
      case 'Vtransform'
        Gout.(field) = nc_read(Ginp,field);
      case 'Vstretching'
        Gout.(field) = nc_read(Ginp,field);
      case 'theta_s'
        Gout.(field) = nc_read(Ginp,field);
      case 'theta_b'
        Gout.(field) = nc_read(Ginp,field);
      case 'Tcline'
        Gout.(field) = nc_read(Ginp,field);
      case 'hc'
        Gout.(field) = nc_read(Ginp,field);
      case {'s_rho', 'sc_r'}
        Gout.(field) = nc_read(Ginp,field);
        Gout.N = length(Gout.(field));
        got.N  = true;
      case 'Cs_r'
        Gout.(field) = nc_read(Ginp,field);
      case {'s_w', 'sc_w'}
        Gout.(field) = nc_read(Ginp,field);
      case 'Cs_w'
        Gout.(field) = nc_read(Ginp,field);
      case 'zeta'
        process.vertical = true;
        got.zeta  = true;
        zeta_file = Ginp;
    end
  end

% If extracted from finer grid, get coarseness factor.

  got.coarse_factor = any(strcmp(anames,'coarse_factor'));
  if (got.coarse_factor)
    index = strcmp(anames,'coarse_factor');
    Gout.coarse_factor = double(Ginfo.Attributes(index).Value);

    index = strcmp(anames,'parent_Imin');
    Gout.parent_Imin   = double(Ginfo.Attributes(index).Value);
    index = strcmp(anames,'parent_Imax');
    Gout.parent_Imax   = double(Ginfo.Attributes(index).Value);

    index = strcmp(anames,'parent_Jmin');
    Gout.parent_Jmin   = double(Ginfo.Attributes(index).Value);
    index = strcmp(anames,'parent_Jmax');
    Gout.parent_Jmax   = double(Ginfo.Attributes(index).Value);
  end

% If refinement grid, get refinement factor.

  got.refine_factor = any(strcmp(anames,'refine_factor'));
  if (got.refine_factor)
    index = strcmp(anames,'refine_factor');
    Gout.refine_factor = double(Ginfo.Attributes(index).Value);

    index = strcmp(anames,'parent_Imin');
    Gout.parent_Imin   = double(Ginfo.Attributes(index).Value);
    index = strcmp(anames,'parent_Imax');
    Gout.parent_Imax   = double(Ginfo.Attributes(index).Value);

    index = strcmp(anames,'parent_Jmin');
    Gout.parent_Jmin   = double(Ginfo.Attributes(index).Value);
    index = strcmp(anames,'parent_Jmax');
    Gout.parent_Jmax   = double(Ginfo.Attributes(index).Value);
  end

% If vertical parameters "Vtransform" and "Vstretching" are not found
% in primary file "Ginp", set their default values for backward
% compatibility.

  if (process.vertical)  
    if (~got.Vtransform)
      Gout.Vtransform = 1;
      got.Vtransform  = true;   
    end

    if (~got.Vstretching)
      Gout.Vtransform = 1;
      got.Vstretching = true;
    end
  end
  
end

%--------------------------------------------------------------------------
% The "Sinp" argument is a structure array containing application
% vertical coordinate parameters.
%--------------------------------------------------------------------------

if (process.parameters)
  
  parlist = {'N', 'Vtransform', 'Vstretching',                          ...
             'theta_s', 'theta_b', 'Tcline', 'hc'};

  for par = parlist
    field = char(par);
    if (isfield(Sinp,field))
       Gout.(field) = Sinp.(field);
       got.(field)  = true;
    else
      error([' GET_ROMS_GRID: unable to find field "',field,'", in',    ...
             ' in structure: Sinp']);
    end
  end

  process.vertical = true;

end

%--------------------------------------------------------------------------
% The "Sinp" argument is a secondary ROMS output file.  Use the vertical
% coordinates parameters from secodary file to compute depths. Overwrite
% their values in "Gout" structure.
%--------------------------------------------------------------------------

if (process.zeta)
  if (ischar(Sinp))
    Sinfo = nc_inq(Sinp);
    NvarsS = length(Sinfo.Variables);

    got.N           = false;
    got.Vtransform  = false;
    got.Vstretching = false;
    got.theta_s     = false;
    got.theta_b     = false;
    got.Tcline      = false;
    got.hc          = false;
    got.s_rho       = false;
    got.Cs_r        = false;
    got.s_w         = false;
    got.Cs_w        = false;
    got.zeta        = false;

    for n = 1:NvarsS
      field = char(Sinfo.Variables(n).Name);
      switch field
        case 'Vtransform'
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case 'Vstretching'
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case 'theta_s'
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case 'theta_b'
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case 'Tcline'
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case 'hc'
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case {'s_rho', 'sc_r'}
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
          Gout.N = length(Gout.(field));
          got.N  = true;
        case 'Cs_r'
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case {'s_w', 'sc_w'}
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case 'Cs_w'
          Gout.(field) = nc_read(Sinp,field);
          got.(field)  = true;
        case 'zeta'
          got.(field) = true;
          zeta_file = Sinp;
          process.vertical = true;
      end
    end

% If vertical parameters "Vtransform" and "Vstretching" are not found
% in secondary file, set their default values for backward compatibility.
    
    if (~got.Vtransform)
      Gout.Vtransform  = 1;
      got.Vtransform   = true;
    end

    if (~got.Vstretching)
      Gout.Vstretching = 1;
      got.Vstretching  = true;
    end
    
  end
end

%--------------------------------------------------------------------------
% Add grid variables to structure, except vertical depths.
%--------------------------------------------------------------------------

% If appropriate, read in fields from primary file "Ginp".

if (process.horizontal)
  for var = varhor
    field = char(var);
    if (got.(field))
      Gout.(field) = nc_read(Ginp,field);
    else
      Gout.(field) = [];
    end
  end

  if (got.h)
    [Lr,Mr]=size(Gout.h);
    L = Lr-1;  Lm=L-1;
    M = Mr-1;  Mm=M-1;

    Gout.Lm = Lm;                %  This are horizontal (Lm,Mm) dimensions
    Gout.Mm = Mm;                %  that are specified in ROMS input script
                                 %  RHO-points: Lp = Lm+1,  Mp = Mm+2  

    if (~got.mask_rho)
      Gout.mask_rho = ones(Lr,Mr);
      got.mask_rho  = true;
    end
    if (~got.mask_psi)
      Gout.mask_psi = ones(L,M);
      got.mask_psi  = true;
    end
    if (~got.mask_u)
      Gout.mask_u   = ones(L,Mr);
      got.mask_u    = true;
    end
    if (~got.mask_v)
      Gout.mask_v   = ones(Lr,M);
      got.mask_v    = true;
    end
  
    if (~got.angle)
      Gout.angle = zeros(Lr,Mr);
      got.angle  = true;
    end
  end

% Extract boundary conditions locations.

  if (spherical)
    if (got.lon_rho)
      Gout.lon_rho_west  = Gout.lon_rho(1,:);
      Gout.lon_rho_east  = Gout.lon_rho(end,:);
      Gout.lon_rho_south = Gout.lon_rho(:,1);
      Gout.lon_rho_north = Gout.lon_rho(:,end);
    end
    if (got.lat_rho)
      Gout.lat_rho_west  = Gout.lat_rho(1,:);
      Gout.lat_rho_east  = Gout.lat_rho(end,:);
      Gout.lat_rho_south = Gout.lat_rho(:,1);
      Gout.lat_rho_north = Gout.lat_rho(:,end);
    end

    if (got.lon_u)
      Gout.lon_u_west    = Gout.lon_u(1,:);
      Gout.lon_u_east    = Gout.lon_u(end,:);
      Gout.lon_u_south   = Gout.lon_u(:,1);
      Gout.lon_u_north   = Gout.lon_u(:,end);
    end
    if (got.lat_u)
      Gout.lat_u_west    = Gout.lat_u(1,:);
      Gout.lat_u_east    = Gout.lat_u(end,:);
      Gout.lat_u_south   = Gout.lat_u(:,1);
      Gout.lat_u_north   = Gout.lat_u(:,end);
    end

    if (got.lon_v)
      Gout.lon_v_west    = Gout.lon_v(1,:);
      Gout.lon_v_east    = Gout.lon_v(end,:);
      Gout.lon_v_south   = Gout.lon_v(:,1);
      Gout.lon_v_north   = Gout.lon_v(:,end);
    end
    if (got.lat_v)
      Gout.lat_v_west    = Gout.lat_v(1,:);
      Gout.lat_v_east    = Gout.lat_v(end,:);
      Gout.lat_v_south   = Gout.lat_v(:,1);
      Gout.lat_v_north   = Gout.lat_v(:,end);
    end
  else
    if (got.x_rho)
      Gout.x_rho_west  = Gout.x_rho(1,:);
      Gout.x_rho_east  = Gout.x_rho(end,:);
      Gout.x_rho_south = Gout.x_rho(:,1);
      Gout.x_rho_north = Gout.x_rho(:,end);
    end
    if (got.y_rho)
      Gout.y_rho_west  = Gout.y_rho(1,:);
      Gout.y_rho_east  = Gout.y_rho(end,:);
      Gout.y_rho_south = Gout.y_rho(:,1);
      Gout.y_rho_north = Gout.y_rho(:,end);
    end

    if (got.x_u)
      Gout.x_u_west    = Gout.x_u(1,:);
      Gout.x_u_east    = Gout.x_u(end,:);
      Gout.x_u_south   = Gout.x_u(:,1);
      Gout.x_u_north   = Gout.x_u(:,end);
    end
    if (got.y_u)
      Gout.y_u_west    = Gout.y_u(1,:);
      Gout.y_u_east    = Gout.y_u(end,:);
      Gout.y_u_south   = Gout.y_u(:,1);
      Gout.y_u_north   = Gout.y_u(:,end);
    end

    if (got.x_v)
      Gout.x_v_west    = Gout.x_v(1,:);
      Gout.x_v_east    = Gout.x_v(end,:);
      Gout.x_v_south   = Gout.x_v(:,1);
      Gout.x_v_north   = Gout.x_v(:,end);
    end
    if (got.y_v)
      Gout.y_v_west    = Gout.y_v(1,:);
      Gout.y_v_east    = Gout.y_v(end,:);
      Gout.y_v_south   = Gout.y_v(:,1);
      Gout.y_v_north   = Gout.y_v(:,end);
    end
  end

% Extract perimeter.

  if (spherical)
    if (got.lon_psi && got.lat_psi)
      [L,M]=size(Gout.lon_psi);
      Gout.lon_perimeter = [squeeze(Gout.lon_psi(1:L,1));               ...
                            squeeze(Gout.lon_psi(L,2:M))';              ...
                            squeeze(flipud(Gout.lon_psi(1:Lm,M)));      ...
                            squeeze(fliplr(Gout.lon_psi(1,1:Mm)))'];

      Gout.lat_perimeter = [squeeze(Gout.lat_psi(1:L,1));               ...
                            squeeze(Gout.lat_psi(L,2:M))';              ...
                            squeeze(flipud(Gout.lat_psi(1:Lm,M)));      ...
                            squeeze(fliplr(Gout.lat_psi(1,1:Mm)))'];
    end
  else
    if (got.x_psi && got.x_psi)
      [L,M]=size(Gout.x_psi);
      Gout.x_perimeter = [squeeze(Gout.x_psi(1:L,1));                   ...
                          squeeze(Gout.x_psi(L,2:M))';                  ...
                          squeeze(flipud(Gout.x_psi(1:Lm,M)));          ...
                          squeeze(fliplr(Gout.x_psi(1,1:Mm)))'];

      Gout.y_perimeter = [squeeze(Gout.y_psi(1:L,1));                   ...
                          squeeze(Gout.y_psi(L,2:M))';                  ...
                          squeeze(flipud(Gout.y_psi(1:Lm,M)));          ...
                          squeeze(fliplr(Gout.y_psi(1,1:Mm)))'];
    end
  end
  
% Determine "uniform", "curvilinear", and "vector_rotation" switches.

  if (got.pm && got.pn)
    if (length(unique(Gout.pm(:))) == 1 &&                              ...
        length(unique(Gout.pn(:))) == 1)
      Gout.uniform = true;
    end

    if (length(unique(Gout.pm(:))) > 1 ||                               ...
        length(unique(Gout.pn(:))) > 1)
      Gout.curvilinear = true;
    end
  end
  
  if (got.angle)
    if (length(unique(Gout.angle(:))) > 1 ||                            ...
               unique(Gout.angle(:))  > 0)
      Gout.vector_rotation = true;
    end
  end

% If available, process coastline data.

  if (got.lon_coast)
    Gout.lon_coast = nc_read(Ginp,'lon_coast');
    Gout.lat_coast = nc_read(Ginp,'lat_coast');
  end

end

%--------------------------------------------------------------------------
% Add vertical depths.
%--------------------------------------------------------------------------

if (process.vertical)

  if (~got.Vtransform  || isempty(Gout.Vtransform ))
    error([' GET_ROMS_GRID: unassigned field ''Vtransform''',           ...
           ' in structure: Gout']);
  end
  if (~got.Vstretching || isempty(Gout.Vstretching))
    error([' GET_ROMS_GRID: unassigned field ''Vstretching''',          ...
           ' in structure: Gout']);
  end
  if (~got.theta_s     || isempty(Gout.theta_s    ))
    error([' GET_ROMS_GRID: unassigned field ''theta_s''',              ...
           ' in structure: Gout']);
  end
  if (~got.theta_b     || isempty(Gout.theta_b    ))
    error([' GET_ROMS_GRID: unassigned field ''theta_b''',              ...
           ' in structure: Gout']);
  end
  if (~got.hc          || isempty(Gout.hc         ))
    error([' GET_ROMS_GRID: unassigned field ''hc''',                   ...
           ' in structure: Gout']);
  end
  if (~got.N           || isempty(Gout.N          ))
    error([' GET_ROMS_GRID: unassigned field ''N''',                    ...
           ' in structure: Gout']);
  end      

  h = Gout.h;
  if (~isempty(TimeRecord))
    zeta = nc_read(zeta_file,'zeta',TimeRecord);
  else
    zeta = zeros(size(h));
    Gout.TimeRecord = 'Computing unperturbed depths, zeta=0';
  end
   
  if (isempty(h))
    disp(' ')
    disp('   GET_ROMS_GRID - input file does not have grid data:');
    disp(['            Ginp:  ',Ginp]);
  else
    if (~(got.s_rho || got.Cs_w))
      kgrid = 0;
      [Gout.s_rho,Gout.Cs_r] = stretching(Gout.Vstretching,             ...
                                          Gout.theta_s,                 ...
                                          Gout.theta_b,                 ...
                                          Gout.hc, Gout.N,              ...
                                          kgrid, false);
    end

    if (~(got.s_w || got.Cs_w))
      kgrid = 1;
      [Gout.s_w,  Gout.Cs_w] = stretching(Gout.Vstretching,             ...
                                          Gout.theta_s,                 ...
                                          Gout.theta_b,                 ...
                                          Gout.hc, Gout.N, kgrid);
    end

    igrid = 1;
    Gout.z_r = set_depth(Gout.Vtransform, Gout.Vstretching,             ...
                         Gout.theta_s, Gout.theta_b, Gout.hc,           ...
                         Gout.N, igrid, h, zeta, false);

    igrid = 3;
    Gout.z_u = set_depth(Gout.Vtransform, Gout.Vstretching,             ...
                         Gout.theta_s, Gout.theta_b, Gout.hc,           ...
                         Gout.N, igrid, h, zeta, false);

    igrid = 4;
    Gout.z_v = set_depth(Gout.Vtransform, Gout.Vstretching,             ...
                         Gout.theta_s, Gout.theta_b, Gout.hc,           ...
                         Gout.N, igrid, h, zeta, false);

    igrid = 5;
    Gout.z_w = set_depth(Gout.Vtransform, Gout.Vstretching,             ...
                         Gout.theta_s, Gout.theta_b, Gout.hc,           ...
                         Gout.N, igrid, h, zeta, false);

    N = Gout.N;
    Gout.Hz = Gout.z_w(:,:,2:N+1) - Gout.z_w(:,:,1:N);
  end

end

return

end



