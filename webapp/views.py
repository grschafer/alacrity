from flask import render_template, request, session, send_from_directory, jsonify

from webapp import app, db


#@app.route('/favicon.ico')
#def favicon():
#    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/matches/', methods=['GET'])
def matches_index():
    result = list(db.find({}, {'match_id':1, '_id':0}))
    id_list = [x['match_id'] for x in result]
    return jsonify(matches=id_list)

@app.route('/wards/<int:match_id>', methods=['GET'])
def wards_match(match_id):
    match = db.find_one({'match_id':match_id})
    return jsonify(wards=match['wards'])

