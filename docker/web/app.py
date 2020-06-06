from flask import Flask, render_template

app = Flask(__name__)


@app.route('/')
def welcome():
    """Top welcome page."""
    template = 'welcome.html'

    values = {
        "aa": "bjc"
    }

    return render_template(template, **values)


@app.route('/builder', methods=['POST', 'GET'])
def builder():
    """Builder page with python input."""
    import os
    import subprocess
    from flask import request

    template = 'builder.html'
    values = {}
    diag_folder = "static/diagrams/"

    code = request.form.get('code')
    if code:
        # clean the directory
        _, _, filenames = next(os.walk(diag_folder))
        for one_file in filenames:
          os.remove('%s%s' % (diag_folder, one_file))
        # write the code in a file and execute
        with open("%stemp_code.py" % diag_folder, "w") as f:
            f.write(code)
        result = subprocess.run(["python3", "temp_code.py"], cwd=diag_folder, capture_output=True)
        # TODO get the result if there's error to display on the template
        print('stdout: ', result.stdout)
        print('stderr: ', result.stderr)
        # delete the temp file
        os.remove("%stemp_code.py" % diag_folder)
        # get the pic to display
        _, _, filenames = next(os.walk(diag_folder))
        pic_name = filenames[0]
        values.update({
            "code": code,
            "pic_name": pic_name,
        })

    return render_template(template, **values)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
