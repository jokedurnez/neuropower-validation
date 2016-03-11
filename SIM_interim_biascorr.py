############
# preamble #
############

from __future__ import division
import os
import sys
sys.path.append("/share/PI/russpold/software/anaconda/lib/python2.7/site-packages")
pilot_sub = int(sys.argv[1])
final_sub = int(sys.argv[2])
seed = int(sys.argv[3])
pow = float(sys.argv[4])
HOMEDIR = sys.argv[5]
DATADIR = sys.argv[6]
TMPDIR = sys.argv[7]
os.chdir(HOMEDIR)

import numpy as np
import scipy
from scipy.stats import norm, t
import math
import nibabel as nib
import shutil
import csv
import sys
import imp
import BUM
import neuropower
import cluster
import peakdistribution
import simul_multisubject_fmri_dataset
import model
import pandas as pd

TEMPDIR = os.path.join(TMPDIR,"temporary_"+str(seed)+"/")
resfile = os.path.join(DATADIR,"estimation_sim_"+str(seed)+".csv")
if os.path.isfile(resfile):
    os.remove(resfile)

for c in range(16):

    os.mkdir(TEMPDIR)
    os.chdir(TEMPDIR)

    #######################
    # simulate pilot data #
    #######################
    # conditions
    effectsizes = np.repeat([0.5,1,1.5,2],4)
    widths = [2,4,6,8]*4
    es_names = np.repeat(["half","one","onehalf","two"],4)
    wd_names = [2,4,6,8]*4
    #parameters
    exc = 3
    smooth_FWHM = 3
    FWHM = [smooth_FWHM,smooth_FWHM,smooth_FWHM]
    smooth_sigma = smooth_FWHM/(2*math.sqrt(2*math.log(2)))
    mask = nib.load(os.path.join(HOMEDIR,"SIM_mask.nii"))
    width = widths[c]
    effectsize = effectsizes[c]
    # general total dataset
    noise_pilot = simul_multisubject_fmri_dataset.surrogate_3d_dataset(n_subj=final_sub, mask=mask,
                                 sk=smooth_sigma,noise_level=1.0,
                                 width=5.0,out_text_file=None,
                                 out_image_file=None, seed=seed)
    signal = nib.load(os.path.join(HOMEDIR,"SIM_activation"+str(width)+".nii")).get_data()
    signal = np.repeat(signal[:, :, :, np.newaxis], final_sub, axis=3)
    low_values_indices = signal < 0.1
    signal[low_values_indices] = 0
    high_values_indices = signal > 0
    signal[high_values_indices] = effectsize
    noise_pilot = noise_pilot.transpose((1,2,3,0))
    activation = signal[:,:,:,1]
    img=nib.Nifti1Image(activation,np.eye(4))
    img.to_filename("activation.nii.gz")
    data = signal + noise_pilot
    # select pilot data
    data_pilot = data[:,:,:,0:pilot_sub]
    img=nib.Nifti1Image(data_pilot,np.eye(4))
    img.to_filename("simulation.nii.gz")
    # perform second level OLS analysis on simulated data
    model.model(pilot_sub,TEMPDIR)
    fslcmd = 'flameo --copefile=simulation.nii.gz --covsplitfile=design.grp --designfile=design.mat --ld=stats --maskfile=%s --runmode=ols --tcontrastsfile=design.con' %(os.path.join(HOMEDIR,'SIM_mask.nii'))
    os.popen(fslcmd).read()

    # extract peaks

    SPM_t = nib.load("stats/tstat1.nii.gz").get_data()
    p_values = t.cdf(-SPM_t, df = pilot_sub-1)
    SPM_z = -norm.ppf(p_values)
    SPM = SPM_z[::-1,:,:]
    peaks = cluster.cluster(SPM,exc)

    ###############################################################
    # estimate and compute model and estimate power on pilot data #
    ###############################################################

    # compute P-values

    pvalues = np.exp(-exc*(np.array(peaks.peak)-exc))
    pvalues = [max(10**(-6),l) for l in pvalues]
    peaks['pval'] = pvalues

    # estimate model

    bum = BUM.bumOptim(peaks['pval'].tolist(),starts=10)
    if bum['pi1'] == 0:
        est_eff = 'nan'
    else:
        modelfit = neuropower.modelfit(peaks.peak,bum['pi1'],exc=exc,starts=20,method="RFT")
        est_eff = modelfit['mu']
        est_sd = modelfit['sigma']
        tau = neuropower.TruncTau(est_eff,est_sd,exc)
        est_exp_eff = est_eff + tau*est_sd

    # compute true parameters

    truth = []
    for i in range(len(peaks)):
        peak_act = activation[peaks.x[i],peaks.y[i],peaks.z[i]]
        truth.append(peak_act)

    truth = [0 if x == 0 else 1 for x in truth]
    peaks['active'] = truth
    true_indices = [index for index,value in enumerate(truth) if value == 1]
    true_effectsize = np.mean(peaks.peak[true_indices])
    true_sd = np.std(peaks.peak[true_indices])
    true_pi1 = np.mean(truth)

    # write away estimation results with true values

    shutil.rmtree(TEMPDIR)

    if bum['pi1'] == 0:
        estimation = [effectsize, str(wd_names[c]), bum['pi1'],true_pi1,est_eff,true_effectsize,est_exp_eff,est_sd,true_sd,bum['a'],'nan','nan','nan','nan','nan','nan']
        fd = open(resfile,"a")
        wr = csv.writer(fd,quoting=csv.QUOTE_NONE)
        wr.writerow(estimation)
        fd.close()
        shutil.rmtree(TEMPDIR)
        continue

    # predict power
    thresholds = neuropower.threshold(peaks.peak,peaks.pval,FWHM=FWHM,mask=mask,alpha=0.05,exc=exc)
    effect_cohen = modelfit['mu']/np.sqrt(pilot_sub)
    power_predicted = []
    for s in range(pilot_sub,final_sub):
        projected_effect = effect_cohen*np.sqrt(s)
        powerpred =  {k:1-neuropower.altCDF(v,projected_effect,modelfit['sigma'],exc=exc,method="RFT") for k,v in thresholds.items() if v!='nan'}
        power_predicted.append(powerpred)

    pred_power = pd.DataFrame(power_predicted)
    pred_power['newsub'] = range(pilot_sub,final_sub)
    minind = int(np.min([i for i,elem in enumerate(pred_power['UN']>pow,1) if elem]))
    SS = pred_power['newsub'][minind]-1

    ##################
    # add final data #
    ##################

    os.mkdir(TEMPDIR)
    os.chdir(TEMPDIR)

    power_true = []
    data_final = data[:,:,:,0:SS]
    img=nib.Nifti1Image(data_final,np.eye(4))
    img.to_filename("simulation.nii.gz")

    # analyse data and extract peaks
    model.model(SS,TEMPDIR)
    fslcmd = 'flameo --copefile=simulation.nii.gz --covsplitfile=design.grp --designfile=design.mat --ld=stats --maskfile=%s --runmode=ols --tcontrastsfile=design.con' %(os.path.join(HOMEDIR,'SIM_mask.nii'))
    os.popen(fslcmd).read()

    # Without correction

    SPM_c = nib.load("stats/tstat1.nii.gz").get_data()
    p_values = t.cdf(-SPM_t, df = SS-1)
    SPM_z = -norm.ppf(p_values)
    SPM = SPM_z[::-1,:,:]
    peaks = cluster.cluster(SPM,exc)
    pvalues = np.exp(-exc*(np.array(peaks.peak)-exc))
    pvalues = [max(10**(-6),k) for k in pvalues]
    peaks['pval'] = pvalues

    # compute true power for different procedures

    truth = []
    for i in range(len(peaks)):
        peak_act = activation[peaks.x[i],peaks.y[i],peaks.z[i]]
        truth.append(peak_act)

    truth = [0 if x == 0 else 1 for x in truth]
    peaks['active'] = truth
    thresholds = neuropower.threshold(peaks.peak,peaks.pval,FWHM=FWHM,mask=mask,alpha=0.05,exc=exc)
    if np.sum(peaks.peak>thresholds['UN']) == 0:
        TPR_u = 0
        FPR_u = 0
    else:
        pos = peaks.peak>thresholds['UN']
        true = peaks.active==1
        TP = [a and b for a,b in zip(pos,true)]
        FP = [a and not b for a,b in zip(pos,true)]
        TPR_u = float(np.sum(TP))/float(np.sum(true))
        FPR_u = float(np.sum(FP))/float(len(peaks)-np.sum(true))

    # with correction

    SPM_B = nib.load("stats/cope1.nii.gz").get_data()
    SPM_SE = nib.load("stats/varcope1.nii.gz").get_data()
    SPM_VAR = SPM_SE*SS
    v = (thresholds["UN"]-scipy.stats.norm.ppf(0.2))**2/est_eff**2
    SPM_VAR_BC = SPM_VAR +(pilot_sub-1)/(pilot_sub-2)*1/v
    SPM_SE_BC = SPM_VAR_BC/SS
    SPM_t = SPM_B/np.sqrt(SPM_SE_BC)
    p_values = t.cdf(-SPM_t, df = SS-1)
    SPM_z = -norm.ppf(p_values)
    SPM = SPM_z[::-1,:,:]
    peaks = cluster.cluster(SPM,exc)
    pvalues = np.exp(-exc*(np.array(peaks.peak)-exc))
    pvalues = [max(10**(-6),k) for k in pvalues]
    peaks['pval'] = pvalues

    # compute true power for different procedures

    truth = []
    for i in range(len(peaks)):
        peak_act = activation[peaks.x[i],peaks.y[i],peaks.z[i]]
        truth.append(peak_act)

    if np.sum(len(peaks)) == 0:
        TPR_c = 'nan'
        FPR_c = 0
    else:
        truth = [0 if x == 0 else 1 for x in truth]
        peaks['active'] = truth
        thresholds = neuropower.threshold(peaks.peak,peaks.pval,FWHM=FWHM,mask=mask,alpha=0.05,exc=exc)
        if np.sum(peaks.peak>thresholds['UN']) == 0:
            TPR_c = 0
            FPR_c = 0
        else:
            pos = peaks.peak>thresholds['UN']
            true = peaks.active==1
            notrue = np.sum(true)
            nofalse = len(peaks)-np.sum(true)
            TP = [a and b for a,b in zip(pos,true)]
            FP = [a and not b for a,b in zip(pos,true)]
            TPR_c = float(np.sum(TP))/notrue if notrue>0 else 'nan'
            FPR_c = float(np.sum(FP))/nofalse if nofalse>0 else 0

    discr = scipy.stats.norm.cdf(exc,est_eff,est_sd)

    estimation = [effectsize, str(wd_names[c]), bum['pi1'],true_pi1,est_eff,true_effectsize,est_exp_eff,est_sd,true_sd,bum['a'],SS,TPR_u,FPR_u,TPR_c,FPR_c,discr]
    fd = open(resfile,"a")
    wr = csv.writer(fd,quoting=csv.QUOTE_NONE)
    wr.writerow(estimation)
    fd.close()
    shutil.rmtree(TEMPDIR)
