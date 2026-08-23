from flask import Flask, request

app = Flask(__name__)

print_queue = []
next_job_id = 1

attendees = {}


@app.route("/check-in", methods=["POST"])
def check_in():
    global next_job_id

    data = request.get_json()

    attendee_id = data["attendee_id"]
    name = data["name"]

    # Check whether this attendee has already been processed
    if attendee_id in attendees:
        return {
            "status": "duplicate",
            "message": "Attendee has already been processed",
            "attendee": attendees[attendee_id]
        }, 200

    # Create a new print job
    job = {
        "job_id": f"job-{next_job_id:03d}",
        "attendee_id": attendee_id,
        "name": name
    }

    # Move the job ID counter forward
    next_job_id += 1

    # Put the print job into the queue
    print_queue.append(job)

    # Remember that this attendee is now waiting for their badge
    attendees[attendee_id] = {
        "name": name,
        "status": "PRINT_PENDING",
        "job_id": job["job_id"]
    }

    print("Print job added to queue!")
    print(job)

    print("Current queue:")
    print(print_queue)

    print("Attendee statuses:")
    print(attendees)

    return {
        "status": "pending",
        "job": job
    }, 200


@app.route("/next-job", methods=["GET"])
def next_job():
    if not print_queue:
        return {
            "status": "empty",
            "message": "No print jobs available"
        }, 200

    job = print_queue.pop(0)

    print("Job delivered to printer:")
    print(job)

    return job, 200


# Printer tells us when printing is complete
@app.route("/print-webhook", methods=["POST"])
def print_webhook():
    data = request.get_json()

    job_id = data["job_id"]
    attendee_id = data["attendee_id"]
    status = data["status"]

    print("Printer webhook received!")
    print(data)

    if attendee_id in attendees:
        if status == "PRINTED":
            attendees[attendee_id]["status"] = "CHECKED_IN"

    return {
        "status": "received"
    }, 200


if __name__ == "__main__":
    app.run(port=5000)