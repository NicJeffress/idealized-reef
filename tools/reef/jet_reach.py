import sys, netCDF4, numpy as np
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
d=netCDF4.Dataset(sys.argv[1]); out=sys.argv[2]; d.set_auto_mask(False)
def rd(n,k):
    f=np.array(d[n][k],float); f[np.abs(f)>1e30]=0; return f
H=d['h'][:]; yr=d['y_rho'][:,0]; xr=d['x_rho'][0,:]; yv=d['y_v'][:,0]; xv=d['x_v'][0,:]; pm=d['pm'][:]
t=d['ocean_time'][:]/3600; t=t-t[0]
Dx_v=2/(pm[1:,:]+pm[:-1,:])
def q(k):
    z=rd('zeta',k); D=H+z
    Dv=.5*(D[1:]+D[:-1]); Du=.5*(D[:,1:]+D[:,:-1])
    qv=(rd('vbar',k)+rd('vbar_stokes',k))*Dv; qu=(rd('ubar',k)+rd('ubar_stokes',k))*Du
    return qu,qv
nt=len(t); QP=np.zeros((nt,len(yv))); Qnet=QP.copy(); peak=QP.copy(); wid=QP.copy(); qcent=QP.copy()
ic=np.argmin(abs(xv)); mean_u=0; mean_v=0; n=0
L=H.shape[1]-2
for k in range(nt):
    qu,qv=q(k)
    qi=qv[:,1:L+1]; dx=Dx_v[:,1:L+1]
    QP[k]=np.sum(np.maximum(qi,0)*dx,1); Qnet[k]=np.sum(qi*dx,1); peak[k]=qi.max(1); qcent[k]=qv[:,ic]
    for j in range(len(yv)):
        s=QP[k,j]; wid[k,j]=s/max(peak[k,j],1e-9)
    if t[k]>=12: mean_u=mean_u+qu; mean_v=mean_v+qv; n+=1
mean_u=mean_u/n; mean_v=mean_v/n
np.savez(out+'/jet.npz',t=t,yv=yv,QP=QP,Qnet=Qnet,peak=peak,wid=wid)
print('hour: positive offshore transport (m3/s) at y km')
ys=[1200,1500,1750,2000,2500,3000,3500,4000,4500,4900]
print('hour '+' '.join(f'{y:>6d}' for y in ys))
for k in (1,2,3,4,6,8,10,12,15,18,21,24):
    print(f'{t[k]:4.0f} '+' '.join(f'{QP[k,np.argmin(abs(yv-y))]:6.0f}' for y in ys))
pmean=QP[t>=12].mean(0); cm=peak[t>=12].mean(0); wm=wid[t>=12].mean(0)
print('hours 12-24 mean: y, Q+, peak q (m2/s), effective width (m), net')
for y in ys: 
    j=np.argmin(abs(yv-y)); print(y,round(pmean[j]),round(cm[j],2),round(wm[j]),round(Qnet[t>=12].mean(0)[j]))
# time-mean jet: row-integrated positive transport of the time-mean field
vm=mean_v[:,1:L+1]; QPm=np.sum(np.maximum(vm,0)*Dx_v[:,1:L+1],1)
print('positive transport of the 12-24 h MEAN field:',[ (y,round(QPm[np.argmin(abs(yv-y))])) for y in ys])
# front: furthest y at which peak q exceeds thresholds, each hour
for thr in (0.5,1.0,2.0):
    print('front y(m), peak q >',thr,':',[ (int(t[k]),int(yv[np.where(peak[k]>thr)[0][-1]]) if (peak[k]>thr).any() else 0) for k in (1,2,3,4,6,8,12,18,24)])
# Fig 1 maps
ur=np.zeros_like(H); vr=np.zeros_like(H)
def rho(qu,qv):
    u=np.zeros_like(H); v=np.zeros_like(H); u[:,1:-1]=.5*(qu[:,:-1]+qu[:,1:]); v[1:-1]=.5*(qv[:-1]+qv[1:]); return u,v
hours=[3,6,12,18,24]
fig,ax=plt.subplots(2,3,figsize=(15,10.6),sharex=True,sharey=True,constrained_layout=True)
x,y=d['x_rho'][:]/1e3,d['y_rho'][:]/1e3
vmax=8; latt=[]
step=(6/50)
jj,ii=np.nonzero(d['mask_rho'][:]>0); _,fi=np.unique(np.stack([np.floor(x[jj,ii]/step),np.floor(y[jj,ii]/step)]),axis=1,return_index=True); aj,ai=jj[fi],ii[fi]
for a,h0 in zip(ax.ravel(),hours+['mean']):
    if h0=='mean': u,v=rho(mean_u,mean_v); ttl='mean, hours 12-24'
    else: u,v=rho(*q(int(np.argmin(abs(t-h0))))); ttl=f'hour {h0}'
    s=np.hypot(u,v); s=np.ma.masked_where(d['mask_rho'][:]==0,s)
    pc=a.pcolormesh(x,y,s,shading='nearest',cmap='Blues',vmin=0,vmax=vmax)
    a.contour(x,y,H,levels=[1,2,5,10,20,50,100,200],colors='0.55',linewidths=.4)
    qref=1.0; f=np.minimum(1,qref*2/np.maximum(s,1e-9))
    a.quiver(x[aj,ai],y[aj,ai],(u*f)[aj,ai],(v*f)[aj,ai],color='k',scale_units='xy',scale=qref*2/(.8*step),width=.0016,headwidth=3,headlength=3,headaxislength=2.7)
    a.set_title(ttl,fontsize=13); a.set_ylim(0,5.04)
for a in ax[1]: a.set_xlabel('alongshore (km)')
for a in ax[:,0]: a.set_ylabel('from shore (km)')
fig.colorbar(pc,ax=ax,shrink=.7,label='transport |depth-averaged velocity| x depth, Eulerian + Stokes (m²/s)')
fig.suptitle('A15 default, density 1: transport (arrows clipped at 2 m²/s)',fontsize=15)
fig.savefig(out+'/jet_maps.png',dpi=130)
# Fig 2
fig,ax=plt.subplots(1,3,figsize=(16,5),constrained_layout=True)
pc=ax[0].pcolormesh(t,yv/1e3,qcent.T,shading='nearest',cmap='Blues',vmin=0,vmax=vmax); ax[0].set_ylim(1,5.04)
ax[0].set_xlabel('hours'); ax[0].set_ylabel('from shore (km)'); ax[0].set_title('offshore transport at the pass centre line'); fig.colorbar(pc,ax=ax[0],label='m²/s')
cols=['#9ec5f4','#6da7ec','#3987e5','#184f95','#0d366b']
for h0,c in zip((3,6,12,18,24),cols):
    k=np.argmin(abs(t-h0)); ax[1].plot(yv/1e3,QP[k],color=c,lw=2,label=f'hour {h0}')
ax[1].set_xlim(1,5.04); ax[1].set_ylim(0); ax[1].set_xlabel('from shore (km)'); ax[1].set_ylabel('m³/s'); ax[1].set_title('all offshore-going transport across each row'); ax[1].legend(frameon=False); ax[1].grid(alpha=.3)
for h0,c in zip((3,6,12,18,24),cols):
    k=np.argmin(abs(t-h0)); ax[2].plot(yv/1e3,peak[k],color=c,lw=2,label=f'hour {h0}')
ax[2].set_xlim(1,5.04); ax[2].set_ylim(0); ax[2].set_xlabel('from shore (km)'); ax[2].set_ylabel('m²/s'); ax[2].set_title('peak offshore transport on each row'); ax[2].legend(frameon=False); ax[2].grid(alpha=.3)
fig.savefig(out+'/jet_reach.png',dpi=130)
