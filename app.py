from flask import Flask, render_template, jsonify, request, redirect, url_for

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
    # 로그인 만료 체크기능, 게시물들 로드, 좋아요 갯수, 로그인 돼있을 시 좋아요 여부
    token_receive = request.cookies.get('mycookie')
    try:
        # writings 배열을 반복문 돌린다 ->
        # 각 요소의 총 좋아요 갯수
        # 로그인 되있을 시 bool(게시물id,유저id)로 좋아요 여부에 따라 여기서 far fas 구분해서 보냄
        writings = list(db.writings.find({}))

        if token_receive :
            user_info = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            for writing in writings :
                writing['like_or_unlike'] = 'fas' if bool(db.likes.find_one({'writing_id':str(writing['_id']),'user_id':user_info['id']})) else 'far'
        else:
            for writing in writings:
                writing['like_or_unlike'] = 'far'

        for writing in writings :
            writing['like_count'] = db.likes.count_documents({'writing_id':str(writing['_id'])})

        return render_template('index.html',writings=writings)

    except (jwt.ExpiredSignatureError):
        msg="로그인이 만료되었습니다."
        return render_template('index.html',msg=msg)

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
        return redirect(url_for("home"))

@app.route('/update_like', methods=['POST'])
def updateLike():
    token_receive = request.cookies.get('mycookie')
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({'user_id':payload['id']})
        writing_id_receive = request.form['writing_id_give']
        action_receive = request.form['action_give']
        newData = {
            'writing_id':writing_id_receive,
            'user_id' : user_info['user_id']
        }
        if action_receive == "like" :
            db.likes.insert_one(newData)
        elif action_receive == "unlike" :
            db.likes.delete_one(newData)
        # 카운트 결과를 반환
        count = db.likes.count_documents({'writing_id':writing_id_receive})
        return jsonify({'result':'success','count':count})
    except (jwt.ExpiredSignatureError, jwt.exceptions.DecodeError):
        return redirect(url_for("home"))



if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
