import os

from flask import Flask

app = Flask(__name__)


@app.route("/")
def index():
    return """<!DOCTYPE html>
<html lang="en">
<head><title>Admin Panel</title></head>
<body>
<h1>Admin Panel</h1>
<p>Internal administration console. Restricted.</p>
<!-- %s -->
</body>
</html>""" % os.environ.get("FLAG_F7", "FLAG{ssrf_1nt0_th3_1nt3rn4l_n3t}")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
