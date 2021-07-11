#!/usr/bin/env python
# coding: utf-8

# In[16]:


from flask import Flask, render_template, request
import pickle
import pandas as pd
from werkzeug.utils import secure_filename
from werkzeug.datastructures import  FileStorage
import datetime


rf=pickle.load(open('static/RandomForest.pkl', 'rb'))
ct=pickle.load(open('static/ct_LE.pkl','rb'))
dep=pickle.load(open('static/dep_LE.pkl','rb'))
comp=pickle.load(open('static/comp_LE.pkl','rb'))
payer=pickle.load(open('static/payer_LE.pkl','rb'))
pt=pickle.load(open('static/ptPT.pkl','rb'))

app=Flask(__name__)
import os

UPLOAD_FOLDER = 'static'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')

def upload():
    return render_template("upload.html")

@app.route('/uploader', methods=['GET','POST'])
def uploader():
    if request.method=='POST':
        f=request.files['file']
        fsplit=f.filename.split(".")[-1]
        if fsplit=='xlsx':
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename("test_data.xlsx")))
            schedule=pd.read_excel("static/test_data.xlsx")
        else:
            return "Kindly upload Excel Format File"

        g=request.files['files']
        fsplit=g.filename.split(".")[-1]
        if fsplit=='xlsx':
            g.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename("test_data2.xlsx")))
            weather=pd.read_excel("static/test_data2.xlsx")
        else:
            return "Kindly upload Excel Format File"
        
        
        for i in weather.index:
            weather['dt'][i]=datetime.datetime.fromtimestamp(weather['dt'][i]).strftime('%Y-%m-%d')
    
        weather.rename(columns={'dt':'Dt of Svc'},inplace=True)
        meancol=['temp','feels_like', 'temp_min', 'temp_max', 'pressure', 'humidity', 'wind_speed', 'wind_deg', 'rain_1h',
                   'rain_3h', 'snow_1h', 'snow_3h']
        mdeaincol=['clouds_all', 'weather_id']
        modecol=['weather_main', 'weather_description', 'weather_icon']



        df0=pd.DataFrame()
        for i in meancol:
            df0[i]=weather.groupby('Dt of Svc')[i].mean()
        for j in mdeaincol:
            df0[j]=weather.groupby('Dt of Svc')[j].median()
        for k in modecol:
            df0[k]=weather.groupby('Dt of Svc')[k].agg(pd.Series.mode)
        df0.reset_index(inplace=True)

        df0['Dt of Svc']=pd.to_datetime(df0['Dt of Svc'])
        data=schedule.merge(df0,how='outer',on='Dt of Svc')


        for i in ['rain_1h','rain_3h','snow_1h','snow_3h']:
            data[i].fillna(0,inplace=True)
        data['Month']=data['Dt of Svc'].dt.month
        data['Date']=data['Dt of Svc'].dt.day



        data=data[['Per Nbr', 'Payer Name', 'CPT4 Desc', 'Department', 'clouds_all',
               'Bt Nbr', 'Date', 'snow_3h', 'rain_3h', 'Month', 'weather_id',
               'rain_1h', 'snow_1h', 'Component', 'feels_like']]

        conti_df=data[['Per Nbr','feels_like',
                 'rain_1h',
                 'rain_3h',
                 'snow_1h',
                 'snow_3h','weather_id','Month','Date','clouds_all','Bt Nbr']]

        col=conti_df.columns
        for i in conti_df.columns:
                    if conti_df[i].dtype== float :
                        conti_df[i] = conti_df[i].round(2)

        conti_df=pt.transform(conti_df)
        conti_df=pd.DataFrame(conti_df, columns=col)


        data_cat=data[['CPT4 Desc','Department','Component','Payer Name']]

        data_cat.dropna(inplace=True)
        data_cat['Department']=dep.transform(data_cat['Department'])
        data_cat['CPT4 Desc']=ct.transform(data_cat['CPT4 Desc'])
        data_cat['Component']=comp.transform(data_cat['Component'])
        data_cat['Payer Name']=payer.transform(data_cat['Payer Name'])
        data=pd.concat([data_cat,conti_df],axis=1)


        predrf=rf.predict(data)
        Pred=pd.DataFrame(predrf)
        final=schedule[['Bt Nbr','Per Nbr','Md Rc']]
        final['Shows/No Shows']=Pred
        final_noshow=final[final['Shows/No Shows']==0.0]

        print(final['Shows/No Shows'].value_counts())
        try:
            Percent_No_Show=final['Shows/No Shows'].value_counts()[0]*100/final['Shows/No Shows'].value_counts().sum()
            
        except:
            Percent_No_Show = 0



        return render_template("result.html", msg=Percent_No_Show)
    
if __name__ == '__main__':
    app.run()

