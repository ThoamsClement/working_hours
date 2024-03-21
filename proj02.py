from flask import Flask, render_template, request, redirect, url_for,Response,jsonify
import csv
import datetime
import io
import sqlite3

app = Flask(__name__)

timesheets = []
conn = sqlite3.connect('timesheets.db')
# 辅助函数：获取数据库连接和游标
def get_db_connection():
    conn = sqlite3.connect('timesheets.db')
    conn.row_factory = sqlite3.Row
    return conn

# 创建表格函数
def create_table():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS timesheets
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  job_name TEXT,
                  description TEXT,
                  start_time TIMESTAMP,
                  end_time TIMESTAMP,
                  total_hours REAL)''')  # 添加一个总时数字段
    conn.commit()
    conn.close()

# 添加函数以关闭连接
def close_db_connection(exception=None):
    conn = get_db_connection()
    conn.close()

# 创建表格
create_table()
@app.route('/')
def index():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(total_hours) FROM timesheets")
    total_hours = c.fetchone()[0]  # 获取总时数值
    if total_hours is None:
        total_hours = 0
    
    # 查询所有工时记录
    c.execute("SELECT * FROM timesheets")
    timesheets = c.fetchall()
    conn.close()
    return render_template('index.html', timesheets=timesheets,total_hours=total_hours)


@app.route('/add_timesheet', methods=['POST','GET'])
def add_timesheet():
    job_name = request.form['job_name']
    description = request.form['description']
    start_time_str = request.form['start_time']
    end_time_str = request.form['end_time']
    
    start_time = datetime.datetime.strptime(start_time_str, '%Y-%m-%dT%H:%M')
    end_time = datetime.datetime.strptime(end_time_str, '%Y-%m-%dT%H:%M')
    total_hours = calculate_total_hours(start_time, end_time)

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO timesheets (job_name, description, start_time, end_time,total_hours) VALUES (?, ?, ?, ?,?)",
              (job_name, description, start_time, end_time,total_hours))
    conn.commit()
    conn.close()
    
    return redirect(url_for('index'))

def calculate_total_hours(start_time, end_time):
    time_diff = end_time - start_time
    total_hours = time_diff.total_seconds() / 3600
    return total_hours
@app.route('/download_timesheets_csv')
def download_timesheets_csv():
    output = io.StringIO()
    fieldnames = ['job_name', 'description', 'start_time', 'end_time']
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for timesheet in timesheets:
        writer.writerow(timesheets)
    output.seek(0)
    return Response(output, mimetype='text/csv', headers={'Content-Disposition': 'attachment;filename=timesheets.csv'})
@app.route('/api/total_hours')
def get_total_hours():
    conn = get_db_connection()
    c = conn.cursor()
    
    # 查询总时数
    c.execute("SELECT SUM(total_hours) FROM timesheets")
    total_hours = c.fetchone()[0] or 0
    
    # 查询工时记录
    c.execute("SELECT * FROM timesheets")
    timesheets = [{'job_name': row[1], 'description': row[2], 'start_time': row[3], 'end_time': row[4], 'total_hours': row[5]} for row in c.fetchall()]
    
    conn.close()
    
    return jsonify({'total_hours': total_hours, 'timesheets': timesheets})

@app.route('/view_timesheets')
def view_timesheets():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT SUM(total_hours) FROM timesheets")  # 查询所有记录的总时数
    total_hours = c.fetchone()[0] or 0  # 如果总时数为 None，则将其设置为 0
    c.execute("SELECT * FROM timesheets")  # 查询所有工时记录
    timesheets = c.fetchall()
    conn.close()
    return render_template('view.html', timesheets=timesheets, total_hours=total_hours)
def save_to_csv(data):
    with open('timesheets.csv', mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['job_name', 'description','start_time', 'end_time'])
        writer.writeheader()
        for timesheet in data:
            writer.writerow(timesheet)
@app.route('/api/timesheets')
def get_timesheets():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM timesheets")
    timesheets = c.fetchall()
    conn.close()
    # 将查询结果转换为字典列表并返回 JSON 格式数据
    return jsonify({'timesheets': [dict(timesheet) for timesheet in timesheets]})
@app.route('/delete_timesheet/<int:timesheet_id>', methods=['POST'])
def delete_timesheet(timesheet_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM timesheets WHERE id=?", (timesheet_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))



if __name__ == '__main__':
    app.run(debug=True)
