%% Intro
clear all
clc
close all

%% Things to change
swan_buffer_north=0;
swan_buffer_south=0;
swan_buffer_west=0;
swan_buffer_east=0;

%Lm = 88;%num pts in x direction
%Mn = 98;%num pts in y direction
%coords = 'xy';
%channels = 1;

% streching values
dx_min=20;%(m) min value of dx (this is centered on x=0)
dx_max=40;%(m) max value of dx (this will happen at edges)
dy_min=20;%(m)
dy_max=80;%(m)


width_reef = 6000;%distance along shore (ex -3000 to 3000)
width_jet = 100;%width at the bottom of the reef pass
%Not needed anymore. width_reefcrest_gap=400;%500 (400,100 looks good) (500,100 looks good)
%radius_island = 0;


extent_lagoon = 500;%1.5E3;%inflection point between lagoon and reef flat
extent_reefflat=extent_lagoon+400; %inflection point between reef flat and reef crest
extent_reef = extent_reefflat+100;%transition point from reef crest to variable slope forereef
extent_variable_forereef=extent_reef+100;%transition point from variable slope to constant slope
extent_offshore = 5E3;%end of the domain

depth_channel = 10; %also depth lagoon
depth_reef_flat = 2.0;
depth_reef_crest = 0.5;

slope_forereef=1/10;%0.1;%1/30;%zhang 2011

%taper tuning parameters
scale_lagoon2reefflat=300;%distance from inflection point to asymptotes
scale_reefflat2reefcrest=50;%distance from inflection point to asymptotes
scale_jet=200;%125;%x distance from bottom to asymptote
%not needed anymore scale_reefcrest_gap=100;%x distance from bottom ot asymptote 100


fval=sw_f(0);

%Recommendations
%width_reefcrest_gap=2*(2/3)*scale_jet+width_jet;%400;%500 (400,100 looks good) (500,100 looks good)

%val=10*(abs(depth_reef_crest-depth_reef_flat)/abs(depth_channel-depth_reef_flat));
%scale_reefcrest_gap=val*scale_jet;%val*scale_jet;%(3/2)*scale_jet;%100;%x distance from bottom ot asymptote 100

%% Lets build X

xmin=-0.5*width_reef;
xmax=0.5*width_reef;
dx_midpt=0;%dx min value is centered on 0
dx_std=(1/6)*width_reef;%this changes the streching

%x_test(1)=-0.5*width_reef;
x_test(1)=0;%making this symmetric
counter=1;
while x_test(counter)<0.5*width_reef
    dx=dx_gaussian_NJ(x_test(counter),xmin,xmax, dx_midpt,dx_std,dx_min,dx_max);
    counter=counter+1;
    %y_test=[y_test,y_test+dy];
    x_test(counter)= x_test(counter-1) + dx ; 

end
x_test=x_test';
x_test=vertcat(-1.*flipud(x_test),x_test(2:end));
x=x_test;

%% Lets build Y
ymin=0;
ymax=extent_offshore;
dy_midpt=extent_reef;%dx min value is centered on 0
dy_std=(1/6)*extent_offshore;%this changes the streching

y_test(1)=0;
counter=1;
while y_test(counter)<ymax
    dy=dx_gaussian_NJ(y_test(counter),ymin,ymax, dy_midpt,dy_std,dy_min,dy_max);
    counter=counter+1;
    %y_test=[y_test,y_test+dy];
    y_test(counter)= y_test(counter-1) + dy ; 

end
y=y_test;

%% Gridding

[X, Y] = ndgrid(x, y);

% Swan X and Y
[xswan,yswan]=Swan_buffer_NJ(x,y,swan_buffer_west,swan_buffer_east,swan_buffer_south,swan_buffer_north);
[Xswan, Yswan] = ndgrid(xswan, yswan);

%% Cross Shore: Lagoon,reef flat, reefcrest, changing slope forereef, constant slope forereef
%[h,slope]= tanh_NJ(x, scale, offset,asy_left,asy_right)

%part 1: lagoon to reef flat
[p1,s1]=tanh_NJ(Y, scale_lagoon2reefflat, extent_lagoon ,...
    depth_channel , depth_reef_flat);

%part 2: reef flat to reef crest
[p2,s2]=tanh_NJ(Y, scale_reefflat2reefcrest , extent_reefflat ,...
    depth_reef_flat ,depth_reef_crest);

%part 3: reef crest to forereef.
%slope will vary linearly from 0 at the reef crest to the constant slope of
%the forereef.
%[depth,slope]=forereef_NJ(x,x0,xt,slope_linear,hrc)
[p3,s3]=forereef_NJ(Y,extent_reef,extent_variable_forereef,...
    slope_forereef,depth_reef_crest);

p1=round(p1,3);
p2=round(p2,3);
p3=round(p3,3);

%checking if bathy matches or if we need to taper
%any overlap in the reef flat
ind=(y<extent_reefflat);%this is the zone we could merge in
if sum(p1(1,ind)==p2(1,ind))>0
    ind_12=find(p1(1,ind)==p2(1,ind),1);
else
    min(abs(p1(1,ind)-p2(1,ind)));
    disp('1,2 merge issue: not perfect match, finding closest')
    cff1=abs(p1(1,:)-p2(1,:));
    cff1(~ind)=nan;
    [~,ind_12]=min(cff1);
    
end

ind=(y>extent_reefflat);%this is the zone we could merge in
if sum(p2(1,ind)==p3(1,ind))>0
    ind_23=find(p2(1,:)==p3(1,:) & ind,1);
else
    min(p2(1,ind)-p3(1,ind));
    disp('2,3 merge issue: not perfect match, finding closest')
    cff1=abs(p2(1,:)-p3(1,:));
    cff1(~ind)=nan;
    [~,ind_23]=min(cff1);
end

p4= p1 .* heaviside(-Y+y(ind_12)) + p2.* heaviside(Y-y(ind_12)) .* heaviside(-Y+ y(ind_23)) + p3 .* heaviside( Y - y(ind_23));
s4= s1 .* heaviside(-Y+y(ind_12)) + s2.* heaviside(Y-y(ind_12)) .* heaviside(-Y+ y(ind_23)) + s3 .* heaviside( Y - y(ind_23));

%% taper to create reefpass

%playing rotating reefpass  here
%[Xr,Yr]=rotate_coord(X,Y-extent_reef,30);%so we rotate around the center of the reefcrest

[t2,~]=sech2_elongated_peak_NJ(X,0,width_jet,1,scale_jet);

t1=ones(size(t2));

%taper to remove reef crest
p5 = p4.*t1 + depth_reef_flat .* (1-t1);


%taper to create channel
t2(p5>depth_channel)=1;

p6=p5.*t2 + depth_channel .* (1-t2);

h=p6;
s_alongshore=(h(2:end,:)-h(1:end-1,:))./(X(2:end,:)-X(1:end-1,:));
s_cross_shore= (h(:,2:end)-h(:,1:end-1))./(Y(:,2:end)-Y(:,1:end-1));

%% Lets do some masking
%mask_rho:1=wet,0=dry

mask_rho=ones(size(h));%pre allocate as all wet

if 1==0% no masking ow

west_y=Y(1,:);
west_h=h(1,:);
[~,west_mask_ind]=min(abs(west_y-extent_reef));
mask_rho(1,1:west_mask_ind)=0;%mask from backreef to reefcrest

east_y=Y(end,:);
east_h=h(end,:);
[~,east_mask_ind]=min(abs(east_y-extent_reef));
mask_rho(end,1:east_mask_ind)=0;%mask from backreef to reefcrest

end

%lets mask the south and  sides
mask_rho(:,1)=0;
%mask_rho(:,end)=0;

figure()
pcolorjw(X,Y,mask_rho);
shading flat
title('masking 1=wet, 0 is dry')


%%  Sponge Viscosity and Diffusivity

visc_factor=ones(size(h));
diff_factor=ones(size(h));

visc_factor_min=1;
visc_factor_max=5000;

diff_factor_min=1;
diff_factor_max=5000;

visc_diff_ribbon_width=10;

% lets get how far indicies are from an edge
dist_from_edge=zeros(size(h));
for i=1:size(h,1)
    for j=1:size(h,2)
    dist_from_edge(i,j) = min([i-1 ,j-1 , size(h,1)-i, size(h,2)-j]);
    end
end

%y=mx+b;viscosity
slope=(visc_factor_min-visc_factor_max)/visc_diff_ribbon_width;
visc_factor= visc_factor_max + slope .* dist_from_edge;
visc_factor(visc_factor<1)=1;

slope=(diff_factor_min-diff_factor_max)/visc_diff_ribbon_width;
diff_factor= diff_factor_max + slope .* dist_from_edge;
diff_factor(diff_factor<1)=1;

ind= (Y<=extent_reef) & (X>-extent_reef) & (X<extent_reef);
visc_factor(ind)=1;
diff_factor(ind)=1;

%making the south boundary smoother
for i=1:visc_diff_ribbon_width
visc_factor(:,i)=visc_factor(:,visc_diff_ribbon_width+1);
diff_factor(:,i)=diff_factor(:,visc_diff_ribbon_width+1);
end

figure()
pcolorjw(X,Y,visc_factor);
shading flat
colorbar


%% Plotting

figure();
surf(X,Y,-log10(h));

%along shore profiles at various offshore y indices
figure();
hold on
for i=[extent_reef:100:extent_reef+500]
    [~,ind]=min(abs(Y(1,:)-i));%getting reef crest y index
    plot(X(:,ind),-h(:,ind),'.-','DisplayName',num2str(i)) ;
end
legend
title([' offshore'])

%along shore profiles at various y indices
figure();
hold on


for i=linspace(extent_reef,extent_lagoon,8)
    [~,ind]=min(abs(Y(1,:)-i));%getting reef crest y index
    plot(X(:,ind),-h(:,ind),'.-','DisplayName',num2str(i)) ;
end
legend
title([' inshore'])

%along shore slope
[~,ind]=min(abs(Y(1,:)-extent_reef));%getting reef crest y index
figure();plot(X(:,ind),-h(:,ind),'.-') ;
yyaxis right
plot(X(2:end,ind),s_alongshore(:,ind),'.-');
title('alongshore')

% cross shore profile
figure();plot(Y(1,:),-h(1,:),'.-');
ylabel('depth')
hold on
yyaxis right
plot(Y(1,:),-s4(1,:),'.-');
ylabel('slope')
xlabel('onshore to off shore')
title('cross shore')

% mesh spacing
figure();
plot(x(2:end),diff(x),'.-');
xlabel('x (m)');
ylabel('dx (m)');
title('X spacing');

figure();
plot(y(2:end),diff(y),'.-');
xlabel('y (m)');
ylabel('dy (m)');
title('Y spacing');

%% lets checkout the west and east boundaries

west_y=Y(1,:);
west_h=h(1,:);
%west_mask=mask_rho(1,:);
%west_h(west_mask==0)=NaN;
west_swan_ind=find(west_h<50,1,'last');


east_y=Y(end,:);
east_h=h(end,:);
%east_mask=mask_rho(end,:);
%east_h(east_mask==0)=NaN;
east_swan_ind=find(east_h<50,1,'last');

figure();
plot(east_y,-east_h,'r');
hold on
plot(east_y(east_swan_ind),-east_h(east_swan_ind),'r*');
plot(west_y,-west_h,'b');
plot(west_y(west_swan_ind),-west_h(west_swan_ind),'b*');

disp(['west swan boundary ind = ',num2str(west_swan_ind)])
disp(['east swan boundary ind = ',num2str(east_swan_ind)])

%% Lets look at grid stiffness
[rx0,rx0_1,rx0_2] = grid_stiffness_Beckmann_Haidvogel_NJ(h);

%[dtfast] = barotropic_cg_courtant_NJ(X,Y,h);
%Cg_max = maxi,j{dtfast √𝑔ℎ(1/𝑑𝑥2 + 1/𝑑𝑦2)}



%%

%%%%% --- done with math stuff now saving


%% Saving stuff

projection = "mercator";
spherical = "F";

if ~exist('mask_rho','var')%is mask_rho a variable in workspace
    mask_rho=ones(size(X));
end


rho.x=X;
rho.y=Y;
rho.depth=h;%depths are positive
rho.mask = mask_rho;%1=wet,0=dry
rho.f=fval.*ones(size(X));



save('Reef_grid_default_1.mat','rho','projection','spherical');
%mat2roms_mw('Reef_grid_default_1.mat', 'roms_grid_default_1.nc')
mat2roms_mw_NJ('Reef_grid_default_1.mat', 'roms_grid_default_1.nc');%hacked to add the f value

add_sponge('roms_grid_default_1.nc', visc_factor, diff_factor);

%% Now buffering for swan grid

clear hswan

%lets grow it in the west-east direction first
% hswan_north=h(:,end);
% hswan_south=h(:,1);
% hswan_west=h(1,:);
% hswan_east=h(end,:);

f1=griddedInterpolant(X,Y,h,'nearest','nearest');
hswan=f1(Xswan,Yswan);

% %hswan[west;h;east]
% hswan=vertcat(ones(swan_buffer_west,size(h,2)).*h(1,:),...
%     h,...
%     ones(swan_buffer_east,size(h,2)).*h(end,:));
% 
% %hswan = [south,hswan,north]
% 
% hswan=horzcat(ones(size(hswan,1),swan_buffer_south).*hswan(:,1),...
%     hswan,...
%     ones(size(hswan,1),swan_buffer_north).*hswan(:,end));

mask_swan=ones(size(Xswan));

f1=griddedInterpolant(X,Y,mask_rho,'nearest','nearest');
mask_swan=f1(Xswan,Yswan);

figure()
surf(Xswan,Yswan,-hswan)
title('swan grid')



%% Now buffering for swan grid _old
% % 
% % clear hswan
% % 
% % %lets grow it in the west-east direction first
% % % hswan_north=h(:,end);
% % % hswan_south=h(:,1);
% % % hswan_west=h(1,:);
% % % hswan_east=h(end,:);
% % 
% % 
% % 
% % %hswan[west;h;east]
% % hswan=vertcat(ones(swan_buffer_west,size(h,2)).*h(1,:),...
% %     h,...
% %     ones(swan_buffer_east,size(h,2)).*h(end,:));
% % 
% % %hswan = [south,hswan,north]
% % 
% % hswan=horzcat(ones(size(hswan,1),swan_buffer_south).*hswan(:,swan_buffer_south+1),...
% %     hswan,...
% %     ones(size(hswan,1),swan_buffer_north).*hswan(:,end));
% % 
% % mask_swan=ones(size(Xswan));
% % 
% % 
% % figure()
% % surf(Xswan,Yswan,-hswan)
% % title('swan grid')


%% Make swan grids

%write_swan_bathy_coord_NJ(x_rho,y_rho,mask_rho,h)
write_swan_bathy_coord_NJ('swan_bathy_default_1.bot','swan_coord_default_1.grd',Xswan,Yswan,mask_swan,hswan)
save('Reef_grid_swan_default_1.mat','Xswan','Yswan','hswan','mask_swan');





%% Subfunctions

function [dx]=dx_gaussian_NJ(x,xmin,xmax, dx_midpt,dx_std,dx_min,dx_max)
%dx_midpt=0.5*(X(end,1)-X(1,1))+X(1,1);
%dx_std=(1/6)*abs(X(1,1)-X(end,1));

dx=normpdf(x,dx_midpt,dx_std);

min_pdf=min([normpdf(xmin,dx_midpt,dx_std),normpdf(xmax,dx_midpt,dx_std)]);
max_pdf=normpdf(dx_midpt,dx_midpt,dx_std);

dx=dx-min_pdf;%now we span some number to zero
dx=dx./(max_pdf-min_pdf);%now we span zero to one to zero
dx=dx.*(dx_max-dx_min);%now we have the correct amplitude
dx=dx_max-dx;
end

function[h,slope]= tanh_NJ(x, scale, offset,asy_left,asy_right)
%this will produce a function between asy_left and asy_right
%INPUTS:
% scale-
%   horizontally streches function, this does not shift inflection
%   point, only streches the funciton equally left and right about inflection
%   point.
%   Here we can think of scale as essentally the distance from our inflection
%   point to the asymptote. More details on this below.
% offset-
%   horizontally shifts inflection point. The inflection point will occur
%   at the value specified by offset
% asy_left-
%   value of the left asymptote
% asy_right-
%   value of the right asymptote

%RECOMMENDATIONS:
%tanh(x)- asymptotes to a value of 1 as x approaches infinity.
%   tanh(3)=0.9951, tanh(2)=0.9640, tanh(1)=0.7616
%
% By changing tanh(x) to tanh(3x), the function will asymptote (0.9951)
% within one unit of x. This allows us to do tanh(3x/scale)
% where scale describes distance from inflection point to
% asymptote. Which is a much more useful physical quantity when building
% grids.

%basic has no vertical shifting or streching
%basic min is zero and max is one
%tanh ranges from -1 to 1, by shifting this up by 1 then dividing by 2 we
%make basic range from 0 to 1. note that when we do this is it
%equivlent to the sigmoid function (2x)

basic= 0.5*(1+tanh(3*(x-offset)/scale));
slope= 0.5* (3/scale)*sech(3*(x-offset)/scale).^2;

%now we are going to normalize basic so it extends from exactly 0 to 1,
%instead of asymptoting to 0 and 1
%basic= (basic-min(basic,[],'all'))./range(basic,'all');
% I found that this wasnt really necessary.
%h=basic;

h=(asy_right-asy_left)*basic+asy_left;
slope= (asy_right-asy_left).*slope;

%after accounting for the vertical streching and shifting, when all is said
%and done. When we are "scale" units away from the inflection point, ( the
%value of h minus the asymptote value ) quantity divided by the range =
%0.9975

%(h(x=offset+scale)-asy_right)/range=0.9975

%idk if this part about the precision is right

end


function [h,hp]=sech2(x,offset,vstrech,scale,c)
%h is function ranging from vstrech to 0 to vstrech
%hp is first derivative with respect to x

h=vstrech+-vstrech*sech((c/scale).*(x-offset)).^2;

hp=(2*vstrech*c/scale).*...
    tanh((c/scale).*(x-offset)).*....
    sech((c/scale).*(x-offset)).^2;

end

function [h,hp]=sech2_elongated_peak_NJ(x,loc,width,vstrech,scale)
%this function ranges from vstrech to 0 to vstrech. The 0 section will be
%horizontally streched "gap" units
c=3;

loc_left=loc-width/2;
loc_right=loc+width/2;

[h_left,hp_left]=sech2(x,loc_left,1,scale,c);%ranges from 1 to 0 to 1
[h_right,hp_right]=sech2(x,loc_right,1,scale,c);%ranges from 1 to 0 to 1


h = h_left .* heaviside(-x+loc_left) + 0 * heaviside(x-loc_left) .* heaviside(-x+ loc_right)+ h_right .* heaviside(x-loc_right);


hp = hp_left .* heaviside(-x+loc_left) + 0 * heaviside(x-loc_left) .* heaviside(-x+ loc_right)+ hp_right .* heaviside(x-loc_right);

end

function [h,hp]=sech2_plateau_NJ(x,loc,width,vstrech,scale)
%this function ranges from vstrech to 0 to vstrech. The 0 section will be
%horizontally streched "gap" units

%max d/dx sech2 is at x=0.658
%sech2(0.658)=0.6670
c=3;

loc_left=loc-width/2;
loc_right=loc+width/2;

[h_left,hp_left]=sech2(x,loc_left,1,scale,c);%ranges from 1 to 0 to 1
[h_right,hp_right]=sech2(x,loc_right,1,scale,c);%ranges from 1 to 0 to 1


h = h_left .* heaviside(-x+loc_left) + 0 * heaviside(x-loc_left) .* heaviside(-x+ loc_right)+ h_right .* heaviside(x-loc_right);
hp = hp_left .* heaviside(-x+loc_left) + 0 * heaviside(x-loc_left) .* heaviside(-x+ loc_right)+ hp_right .* heaviside(x-loc_right);

h(h<=(1/3))=1/3;%forming plateau

hp(h<=(1/3))=0;
h=h-(1/3);

h=h.*(3/2);
hp=h.*(3/2);


end


function [h,hp]=sech2_flip(x,offset,vstrech,scale,c)
%h is function ranging from 0 to vstrech to 0
%hp is first derivative with respect to x

h=vstrech*sech((c/scale).*(x-offset)).^2;

hp=-(2*vstrech*c/scale).*...
    tanh((c/scale).*(x-offset)).*....
    sech((c/scale).*(x-offset)).^2;

end

function [h,slope]=tanh2_NJ(x, scale, offset,gap,asy_sides,asy_middle)
%this function produces a two sided tanh function ranging from asy_sides to
%asy_middle to asy_sides
%the function will be centerd on offset
%INPUTS:
% scale-
%   horizontally streches function, this does not shift inflection
%   point, only streches the funciton equally left and right about both inflection
%   points.
%   Here we can think of scale as essentally the distance from our inflection
%   point to the asymptote.
% offset-
%   horizontally shifts both inflection points. The function will be
%   centered on the value specified by offset
% gap-
%   the distance from the inflection point to the offset value
% asy_sides-
%   value of the left and right asymptote
% asy_middle-
%   the approximate value of the middle

%basic ranges from 0 to 1 to 0
basic= 0.5*(1+tanh((3/scale)*(x-offset+gap)))...%leftside
    -0.5*(1+tanh((3/scale)*(x-offset-gap)));%rightside

slope= 0.5* (3/scale)*sech((3/scale)*(x-offset+gap)).^2 ...
    -0.5* (3/scale)*sech((3/scale)*(x-offset-gap)).^2;

% h=(asy_sides-asy_middle)*basic+asy_middle;
% slope= (asy_sides-asy_middle).*slope;

h=(asy_middle-asy_sides)*basic+asy_sides;
slope= (asy_middle-asy_sides).*slope;
end

function [h,hp] = bathy_reefpass(x,loc,width,asy,hmin,hmax)
%this will create a h ranging from hmin to hmax to hmin
% h will equal hmax for x values of loc-width/2 to loc+width/2
%outside of that range h will taper to hmin, and should converge to hmin
%within asy meters

c=3;%constant is 2 or 3


%preallocating
h=NaN(size(x));
hp=NaN(size(x));

height_of_jet=hmax-hmin;%hoj= height of jet
loc_left=loc-width/2;
loc_right=loc+width/2;

%doing the left side
[h_left,hp_left]=sech2_flip(x,loc_left,height_of_jet,asy,c);%ranges from 0 to hoj to 0
h_left=h_left+hmin;%shifting so now ranges hmin to hmax to hmin

% doing the right side
[h_right,hp_right]=sech2_flip(x,loc_right,height_of_jet,asy,c);%ranges from 0 to hoj to 0
h_right=h_right+hmin;%shifting so now ranges hmin to hmax to hmin


ind=(x<=loc_left);%ind before loc_left

h(ind)=h_left(ind);
hp(ind)=hp_left(ind);

ind=(x>=loc_left & x<=loc_right);%ind between loc_left and loc_right
h(ind)=hmax;
hp(ind)=0;

ind=(x>=loc_right);%ind before loc_left
h(ind)=h_right(ind);
hp(ind)=hp_right(ind);

end


function [x_stretched]=coord_stretch(x, scale, x0)

%scale=3;
%x0=8.5E3;
% """normalized clustering of pts around x0"""
%https://www3.nd.edu/~gtryggva/CFD-Course2017/Lecture-17-2017.pdf

Lx = max(x) - min(x);%length of line segment
xn = (x - min(x))/Lx;%x is now normalized between 0 and 1
xn0 = (x0 - min(x))/Lx;%normalized x0
xc = xn + scale .* (xn0 - xn) .* (1 - xn) .* xn;
x_stretched = xc .* Lx + min(x);
end

function [xswan,yswan]=Swan_buffer_NJ(x,y,swan_buffer_west,swan_buffer_east,swan_buffer_south,swan_buffer_north)
% xswan=[ones(1,swan_buffer_west).*x(1) , x , ones(1,swan_buffer_east).*x(end)];
%
% yswan=[ones(1,swan_buffer_south).*y(1) , y , ones(1,swan_buffer_north).*y(end)];
wascol_x_flag=0;
wascol_y_flag=0;

if iscolumn(x)
    x = x';
    wascol_x_flag=1;
end

if iscolumn(y)
    y = y';
    wascol_y_flag=1;
end

if swan_buffer_west>0
    xswan_left=(swan_buffer_west:-1:1).*(x(1)-x(2)) + x(1);
else
    xswan_left=[];
end

if swan_buffer_east>0
    xswan_right=(1:swan_buffer_east).*(x(end)-x(end-1)) +x(end);
else
    xswan_right=[];
end

if swan_buffer_south>0
    yswan_left=(swan_buffer_south:-1:1).*(y(1)-y(2)) +y(1);
else
    yswan_left=[];
end

if swan_buffer_north>0
    yswan_right=(1:swan_buffer_north).*(y(end)-y(end-1)) +y(end);
else
    yswan_right=[];
end



xswan=[ xswan_left , x , xswan_right];

yswan=[yswan_left, y , yswan_right];

if wascol_x_flag==1
    xswan=xswan';
end

if wascol_y_flag==1
    yswan=yswan';
end
end

function [xswan,yswan]=Swan_buffer_NJ_old(x,y,swan_buffer_west,swan_buffer_east,swan_buffer_south,swan_buffer_north)
% xswan=[ones(1,swan_buffer_west).*x(1) , x , ones(1,swan_buffer_east).*x(end)];
%
% yswan=[ones(1,swan_buffer_south).*y(1) , y , ones(1,swan_buffer_north).*y(end)];

if swan_buffer_west>0
    xswan_left=(swan_buffer_west:-1:1).*(x(1)-x(2)) + x(1);
else
    xswan_left=[];
end

if swan_buffer_east>0
    xswan_right=(1:swan_buffer_east).*(x(end)-x(end-1)) +x(end);
else
    xswan_right=[];
end

if swan_buffer_south>0
    yswan_left=(swan_buffer_south:-1:1).*(y(1)-y(2)) +y(1);
else
    yswan_left=[];
end

if swan_buffer_north>0
    yswan_right=(1:swan_buffer_north).*(y(end)-y(end-1)) +y(end);
else
    yswan_right=[];
end



xswan=[ xswan_left , x , xswan_right];

yswan=[yswan_left, y , yswan_right];
end

function [depth,slope]=forereef_NJ(X,x0,xt,slope_linear,hrc)
%slope of forereef will vary linearly from 0 to desired slope of off shore
%forereef

b=0;
%slope=m(x-x0)+b;
m=(slope_linear -0)/(xt-x0);
slope= m*(X-x0)+b;


%depth = (m/2)*x^2 + (-m*x0 +b)x +c

c = hrc - (m/2).*x0.^2 - (-m * x0 +b).*x0;

depth= (m/2).*X.^2 + (-m*x0 +b).*X +c;

slope(X<x0)=0;
depth(X<x0)=hrc;


%now doing the constant linear slope part

%make sure that streching is consistent in alongshore direction
if ~isequal(X(1,:),unique(X,"rows"))
    error('streching isnt consistent in along shore direction')
end
x=X(1,:);
[~,i]=max(x(x<=xt));%index of max x that is <= xt

%b_linear = depth(1,i)-slope_linear.*xt;

b_linear = depth(1,i)-slope_linear.*x(i);

depth_linear = slope_linear.*X + b_linear;

ind=(X>=xt);
depth(ind)=depth_linear(ind);
slope(ind)=slope_linear;



end

function [Xr,Yr]=rotate_coord(X,Y,theta)

Xr= X .* cosd(theta) + Y .* sind(theta);
Yr= Y .* cosd(theta) - X .* sind(theta);

end


