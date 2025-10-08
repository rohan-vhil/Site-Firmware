from flask import Flask, render_template, request, url_for, flash, redirect
app = Flask(__name__)
import wifi_connect as wcnt
import json 

messages = [{'title': 'Message One',
             'content': 'Message One Content'},
            {'title': 'Message Two',
             'content': 'Message Two Content'} 
            ]

@app.route('/',methods=["POST","GET"])
def index():
    if request.method == 'POST':
        ssid = request.form['ssid']
        password = request.form['password']
        print(ssid,password)
        wcnt.connect(ssid,password)
        if not ssid:
            flash('Title is required!')
        elif not password:
            flash('Content is required!')
        else:
            messages.append({'title': ssid, 'content': password})
            return redirect(url_for('status'))
        #return render_template('base.html')
        #configured = True
        #print(configured)
        #return render_template('login_page.html')
    return render_template('login_page.html', messages=messages)

@app .route('/enter_devices')
def enterDevices():
    return render_template('enter_device.html')

@app.route('/status',methods=["GET"])
def status():
    return render_template('status_page.html',inverter='solar edge')




if __name__ == '__main__': 
    app.run(debug = True,host='0.0.0.0',port = 5000) 