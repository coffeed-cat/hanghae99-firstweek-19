from flask import Flask, render_template, jsonify, request, redirect

app = Flask(__name__)

from pymongo import MongoClient

import jwt
import datetime
import hashlib

SECRET_KEY = 'HappyProject'
client = MongoClient('localhost', 27017)
db = client.selfstudy

@app.route('/', methods=['GET'])
def home():
    # 게시물들 데이터 보내기
    writings = list(db.writings.find({}))
    print(writings)
    return render_template('index.html',writings=writings)

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html')


@app.route('/signup', methods=['GET'])
def signup():
    return render_template('signup.html')


@app.route('/api/login', methods=['POST'])
def api_login():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']
    pw_hashed = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    isThisIdRight = db.users.find_one({'user_id': id_receive, 'user_pw': pw_hashed})

    if isThisIdRight:
        payload = {
            'id': id_receive,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디 또는 비밀번호를 확인해주세요.'})


@app.route('/api/signup', methods=['POST'])
def api_signup():
    id_receive = request.form['id_give']
    pw_receive = request.form['pw_give']

    isThereSameId = db.users.find_one({'user_id': id_receive})

    if isThereSameId:
        return jsonify({'result': 'fail', 'msg': '이미 존재하는 아이디입니다.'})

    pw_hashed = hashlib.sha256(pw_receive.encode('utf-8')).hexdigest()
    newUser = {
        'user_id': id_receive,
        'user_pw': pw_hashed
    }
    db.users.insert_one(newUser);
    return jsonify({'result': 'success', 'msg': '회원가입이 완료되었습니다.'})


@app.route('/write', methods=['POST'])
def write():
    token_receive = request.cookies.get('mycookie')
    print(token_receive)
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        db.users.find_one({'id':payload['id']})
        writer_id = payload['id']
        title_receive = request.form['title_give']
        url_receive = request.form['url_give']
        desc_receive = request.form['desc_give']
        newData = {'title':title_receive,'url':url_receive,'desc':desc_receive,'writer_id':writer_id}
        db.writings.insert_one(newData)
        return jsonify({'result':'success','msg':'작성이 완료되었습니다.'})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return jsonify({'result':'fail'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
