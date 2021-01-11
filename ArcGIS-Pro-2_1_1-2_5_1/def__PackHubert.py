# -*- coding: utf-8 -*-

#'''
#Created on 21 fev. 2013
#Last update on 07 fev. 2014

#@author: Clement Roux

#@contact: samuel.dunesme@ens-lyon.fr
#          CNRS - UMR5600 Environnement Ville Societe
#          15 Parvis Ren� Descartes, BP 7000, 69342 Lyon Cedex 07, France
         
#@note: For each use of the FluvialCorridor toolbox leading to a publication, report, presentation or any other
#       document, please refer the following article :
#       Roux, C., Alber, A., Bertrand, M., Vaudor, L., Piegay, H., submitted. "FluvialCorridor": A new ArcGIS 
#       package for multiscale riverscape exploration. Geomorphology
       
#@summary: def__PackHubert is an open-source python and arcPy code.
#          This code implements the statistical test oh Hubert (Hubert, 2000; Kehagias et al., 2005). Among a
#          numerical series of data, it identifies discontinuities and so, homogeneous segments. For each
#          segment, the mean value is returned.

          
#'''


# Import of required librairies
import numpy as np
from scipy.stats.mstats import mquantiles
import math
import arcpy

#===============================================================================
# CODING
#===============================================================================
def Dstat (x, seg):
    # Dstat : over each segment, Dstat function returns the root mean square.
    ms = model_signal(x, seg)
    Square = [(a-b)**2 for a, b in zip(x,ms)]
    Dstat = np.sum(Square)
    return Dstat



def model_signal(x, seg):
    # model_signal : this function return the mean value over a homogeneous segment.
    # Example : 
    #              x        = [1,1.2,1.1,0.7,22.3,22.1,21.6,102,101.6]
    #         model_signal  = [1,1,1,1,22,22,22,101.8,101.8]
    taille = [(i - j)  for  i,j  in  zip(seg[1:len(seg)],seg[0:len(seg)-1])]
    k=0
    model_signal = []
    for n in taille :
        mean = [float(np.mean([x[k:k+n]]))]*n
        model_signal[k:k+n] = mean[:]
        k+=n
    return model_signal



def segment_signal(seg):
    # segment_signal : assigns a unique ID for each resulting segment.
    taille = [(i - j)  for  i,j  in  zip(seg[1:len(seg)],seg[0:len(seg)-1])]
    segment_signal = []
    k=0
    i=1
    for n in taille[0:len(seg)] :
        temp=[i]*n
        segment_signal[k:len(temp)-1]=temp[:]
        k+=n
        i+=1
    return segment_signal



def Scheffe (x, v_r, k, alpha):
    # Scheffe : this function tests if the difference of mean between two consecutive segments is significant
    #           or not, to validate or reject the segmentation. 
    taille = [(i - j)  for  i,j  in  zip(v_r[1:len(v_r)],v_r[0:len(v_r)-1])]
    n1 = taille[0]
    n2 = taille[1]
    mean=[]
    if n1 == 2 or n1 == 1 :
        mean.append(float(x[0]))
    else :
        mean.append(float(np.mean(x[0:n1])))
    if n2-n1 == 1:
        mean.append(float(n1))
    else :
        mean.append(float(np.mean(x[n1:])))
    diffmean=float(abs(mean[0]-mean[1]))
    dfw = Dstat(x,v_r)/len(x)
    try :
        Sobs = diffmean/(float(np.sqrt(dfw*(1./n1+1./n2))))
        df2 = n1+n2-k
        if df2<=0 :
            df2=abs(df2)+0.01
        F_dist = np.random.f(k-1, df2, 1000000)
        q = list(mquantiles(F_dist,1-alpha))[0]
        Scritical=float(np.sqrt((k-1)*q))
        if (Sobs >= Scritical) :
            test=True
        else :
            test=False
    except ZeroDivisionError :
        test = False                
        
    return dfw, test



def test_segmentation (x, v_r, alpha):
    # test_segmentation : this function tests each segmentation proposed by the Hubert test.
    test = True
    Nelts = len(v_r)
    test2by2 = [float('nan')]*(Nelts-2)
    if (Nelts == 2) :
        test = False
    if (Nelts > 2) :
        for i in range(1,Nelts-1) :
            x_tmp = x[v_r[i-1]:(v_r[i+1])]
            v_r_tmp = [v_r[i-1], v_r[i], v_r[i+1]]
            test2by2[i-1] = Scheffe(x_tmp, v_r_tmp, Nelts-1, alpha)[1]
    for i in (test2by2) :
        if i == False :
            test=False
            
    Dstat_obs = Dstat(x, v_r)

    return [test, test2by2, Dstat_obs]




def Hubert_segmentation (x, alpha, Kmax=float('inf')):
    # Hubert_segmentation : implementation of the Hubert statistical test.
    def dst_calculate (x):
        n=len(x)
        v1=[i+1.0 for i in range(n)]
        v2=np.cumsum(x)
        v3=np.cumsum([i*j for i, j in zip(x,x)])
        vmoy=[i/j for i,j in zip(v2,v1)]
      
        dst=np.zeros((n+1,n))
        dst[n,:] = float('nan')
        dst[0,:] = [k-2*l*j+l*l*i for i, j, k, l in zip(v1,v2,v3,vmoy)]
        
        for i in range (1,n) :
            newv1 = [a-i for a in v1]
            newv2 = [float('nan')]*n
            newv3 = [float('nan')]*n
            newvmoy = [float('nan')]*n
            dst[i,0:i] = float('nan')
            
            newv2[i:] =[(b - v2[i-1]) for b in v2[i:]]
            newv3[i:] =[(c - v3[i-1]) for c in v3[i:]]
            newvmoy[i:] = [(b/a) for a,b in zip(newv1[i:], newv2[i:])]
            
            dst[i,i:] = [(c - 2*d*b + d*d*a) for a, b, c, d in zip(newv1[i:], newv2[i:], newv3[i:], newvmoy[i:])]

        return dst
    
    dst = dst_calculate(x)
    N = len(x)
    c = []
    z = []
    c.append(list(dst[0,:]))
    z.append([0]*N)
    K=1
    mytest = [True]
    
    while (K<=Kmax and mytest[0] == True) :
        c_Km1 = [float('nan')]*(N+1)
        c_Km1[1:len(c_Km1)] = c[K-1]
        cK = [0.0]
        zK = [0]
        for i in range(1, N) :
            ets = []
            rowdst = list(dst[:,i])
            for j in range(len(c_Km1)) :
                ets.append(c_Km1[j] + rowdst[j])
            if i == 1 :
                minimum=ets[1]
                cK.append(minimum)
            if i == 2 :
                temp = [a for a in ets[1:3] if not math.isnan(a)]
                minimum=min(temp)   
                cK.append(minimum)
            if i > 2 :
                temp = [a for a in ets[1:i] if not math.isnan(a)]
                minimum=min(temp)   
                cK.append(minimum)
            elem = []
            elem.append(ets.index(minimum))
            elem = elem[-1]
            zK.append(elem)
            
        c.append([])
        z.append([])
        c[K]=cK
        z[K]=zK
        if (K==1) :
            tKm1 = [0,N]
        if (K>1) :
            tKm1 = tK
        tK = [N]
        for k in range(K,-1,-1) :
            zk = z[k]
            tK.insert(0, zk[tK[0]-1])
        mytest = test_segmentation(x,tK, alpha)
        K+=1
     
    mynewtest=test_segmentation(x,tKm1,alpha)   

    return [tKm1, mynewtest[2]]
