from flask import Flask, render_template

app = Flask(__name__)


@app.route('/', methods=['POST', 'GET'])
def builder():
    """One page app."""
    import os
    import subprocess
    from flask import request

    template = 'app.html'
    values = {}
    diag_folder = "static/diagrams/"

    diagrams_data = request.form.get('diagrams_data')
    if diagrams_data:
        # clean the directory
        _, _, filenames = next(os.walk(diag_folder))
        for one_file in filenames:
          os.remove('%s%s' % (diag_folder, one_file))
        # write the diagrams_data in a file and execute
        with open("%stemp_code.py" % diag_folder, "w") as f:
            f.write(diagrams_data)
        result = subprocess.run(["python3", "temp_code.py"], cwd=diag_folder, capture_output=True)
        # delete the temp file
        os.remove("%stemp_code.py" % diag_folder)
        # if there's error display them on the template
        if result.stderr:
          error_msg = result.stderr.decode("utf-8")
          # clean up the error message
          error_msg = error_msg.replace('File "temp_code.py", ', '')
          values.update({
              "diagrams_data": diagrams_data,
              "error": error_msg
          })
        else:
          # get the pic to display
          _, _, filenames = next(os.walk(diag_folder))
          pic_name = filenames[0]
          values.update({
              "diagrams_data": diagrams_data,
              "pic_name": pic_name,
          })

    return render_template(template, **values)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
