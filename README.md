# Solstice Events Co. — Asynchronous Check-In Service

## 1. Original Requirement

The original check-in system was designed around a synchronous printer API.

When an attendee scanned their QR code, the application would send a print request to the badge printer and wait for the printer to respond before marking the attendee as checked in.

The original flow was:

```text
Attendee scans QR code
        ↓
Application sends print request
        ↓
Application waits for printer response
        ↓
Printing succeeds
        ↓
Attendee is checked in
```

## 2. Pivot / Scope Delta

During the sprint, the badge-printer vendor deprecated the synchronous printing API.

The system therefore had to be changed to an asynchronous model.

The new requirements were to:

* Place print requests into a message queue.
* Avoid waiting for an immediate printer response.
* Keep the attendee in a pending state while printing is in progress.
* Receive a webhook when printing is completed.
* Only mark the attendee as checked in after successful printing.
* Prevent duplicate scans from creating additional badges.
* Handle printer confirmations arriving out of order.

The new flow is:

```text
Attendee scans QR code
        ↓
Print request added to queue
        ↓
Attendee becomes PRINT_PENDING
        ↓
Printer retrieves print job
        ↓
Printer completes printing
        ↓
Printer sends webhook
        ↓
Attendee becomes CHECKED_IN
```

## 3. Implementation

The prototype was implemented using Python and Flask.

### `POST /check-in`

This endpoint receives an attendee's details when their QR code is scanned.

It:

1. Checks whether the attendee has already been processed.
2. Creates a print job for a new attendee.
3. Adds the job to the print queue.
4. Stores the attendee's status as `PRINT_PENDING`.
5. Returns the created job.

Example response for a new attendee:

```json
{
    "status": "pending",
    "job": {
        "job_id": "job-001",
        "attendee_id": "A001",
        "name": "Gloria"
    }
}
```

### `GET /next-job`

This endpoint represents the printer service retrieving the next available print job.

The print queue uses a first-in, first-out (FIFO) approach. The first job added to the queue is the first job retrieved.

If no jobs are available, the endpoint returns:

```json
{
    "status": "empty",
    "message": "No print jobs available"
}
```

### `POST /print-webhook`

This endpoint represents the printer vendor notifying the application when a print job has completed.

When a webhook with a `PRINTED` status is received, the corresponding attendee's status is changed from:

```text
PRINT_PENDING
```

to:

```text
CHECKED_IN
```

Example webhook:

```json
{
    "job_id": "job-001",
    "attendee_id": "A001",
    "status": "PRINTED"
}
```

The endpoint responds with:

```json
{
    "status": "received"
}
```

## 4. Duplicate-Scan Handling

Duplicate-scan protection was maintained after the pivot.

The application stores processed attendees in an `attendees` dictionary. Before creating a new print job, it checks whether the attendee ID already exists.

If the attendee has already been processed, the application returns a duplicate response and does not create another print job.

Example:

```json
{
    "attendee": {
        "job_id": "job-001",
        "name": "Cynthia",
        "status": "CHECKED_IN"
    },
    "message": "Attendee has already been processed",
    "status": "duplicate"
}
```

This demonstrates that an attendee who has already completed the check-in process cannot receive a second badge through another scan.

## 5. Out-of-Order Confirmation

The asynchronous system cannot assume that printer confirmations will arrive in the same order as the original scans.

Three test attendees were processed:

```text
A001 → job-001
A002 → job-002
A003 → job-003
```

The printer confirmations were deliberately sent in a different order:

```text
job-003
job-001
job-002
```

All three attendees were correctly changed to:

```text
CHECKED_IN
```

This demonstrated that the application can process printer confirmations independently rather than relying on the confirmations arriving in the same order as the original check-ins.

## 6. Testing Results

| Test                             | Expected Result                | Result   |
| -------------------------------- | ------------------------------ | -------- |
| New attendee scan                | Print job is created           | ✅ Passed |
| Attendee starts in pending state | Status is `PRINT_PENDING`      | ✅ Passed |
| Retrieve print job               | Job is retrieved from queue    | ✅ Passed |
| Successful printer webhook       | Attendee becomes `CHECKED_IN`  | ✅ Passed |
| Duplicate scan                   | No second print job is created | ✅ Passed |
| Three attendees                  | All three can be processed     | ✅ Passed |
| Out-of-order confirmations       | Correct attendees are updated  | ✅ Passed |

## 7. Technology Used

* **Python** — Application and queue logic.
* **Flask** — HTTP endpoints and webhook handling.
* **Postman** — Testing attendee requests and simulating printer webhook callbacks.
* **Git/GitHub** — Version control and project storage.
* **In-memory Python list** — Used to simulate the vendor's message queue.

## 8. Limitations / Assumptions

This project is a prototype rather than a production system.

The following assumptions and limitations apply:

* The message queue is simulated using an in-memory Python list because the client requirements did not specify a particular message-queue technology.
* The printer service is simulated rather than connected to a real printer.
* Postman was used to simulate printer webhook callbacks during testing.
* Attendee information is stored in memory rather than in a database.
* Data would be lost if the Flask application were restarted.
* The webhook does not currently include authentication or signature verification.

These limitations were accepted to keep the prototype simple and focused on demonstrating the required asynchronous workflow.

## 9. Conclusion

The pivot required the check-in system to move from a synchronous printing model to an asynchronous model.

The implemented solution separates the attendee check-in request from the printer completion response. Print requests are placed into a queue, attendees remain in a `PRINT_PENDING` state while printing is in progress, and a printer webhook changes the status to `CHECKED_IN` after successful printing.

The prototype also maintains duplicate-scan protection and successfully handles printer confirmations arriving out of order.

The solution therefore demonstrates the core requirements of the revised asynchronous check-in system for Solstice Events Co.
