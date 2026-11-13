import requests
r = requests.get('http://127.0.0.1:5000/users/chris_rivers/bookings', timeout=15)
assert r.status_code == 200, r.status_code
