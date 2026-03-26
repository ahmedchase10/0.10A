from langchain.tools import tool
from googleapiclient.discovery import build
from backend.tools.google_auth import get_google_credentials

@tool
def update_attendance(
    spreadsheet_id: str,
    student_name: str,
    date: str,
    status: str
) -> str:
    """Update student attendance in a Google Sheet.
    Use this when the teacher wants to mark attendance.
    Status must be: 'present', 'absent' or 'late'.
    Date format: YYYY-MM-DD."""
    try:
        creds = get_google_credentials()
        service = build("sheets", "v4", credentials=creds)
        sheet = service.spreadsheets()

        result = sheet.values().get(
            spreadsheetId=spreadsheet_id,
            range="Sheet1"
        ).execute()

        values = result.get("values", [])
        headers = values[0] if values else []
        rows = values[1:] if len(values) > 1 else []

        # find student row
        student_row = None
        for i, row in enumerate(rows):
            if row and row[0] == student_name:
                student_row = i + 2  # +2 for header + 1-indexed
                break

        # find date column
        date_col = None
        for i, header in enumerate(headers):
            if header == date:
                date_col = i
                break

        # add date column if not exists
        if date_col is None:
            date_col = len(headers)
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=f"Sheet1!{chr(65 + date_col)}1",
                valueInputOption="RAW",
                body={"values": [[date]]}
            ).execute()

        # add student row if not exists
        if student_row is None:
            student_row = len(rows) + 2
            sheet.values().update(
                spreadsheetId=spreadsheet_id,
                range=f"Sheet1!A{student_row}",
                valueInputOption="RAW",
                body={"values": [[student_name]]}
            ).execute()

        # update cell
        cell = f"Sheet1!{chr(65 + date_col)}{student_row}"
        sheet.values().update(
            spreadsheetId=spreadsheet_id,
            range=cell,
            valueInputOption="RAW",
            body={"values": [[status]]}
        ).execute()

        return f"Attendance updated ✓ {student_name} → '{status}' on {date}"
    except Exception as e:
        return f"Attendance update failed: {str(e)}"

@tool
def get_attendance_report(
    spreadsheet_id: str,
    student_name: str = None
) -> str:
    """Get attendance report from Google Sheets.
    Use this when the teacher wants to check attendance records.
    Optionally filter by student name."""
    try:
        creds = get_google_credentials()
        service = build("sheets", "v4", credentials=creds)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range="Sheet1"
        ).execute()

        values = result.get("values", [])
        if not values:
            return "No attendance data found."

        headers = values[0]
        rows = values[1:]

        if student_name:
            student_rows = [r for r in rows if r and r[0] == student_name]
            if not student_rows:
                return f"No attendance data found for {student_name}."
            report = f"Attendance for {student_name}:\n"
            for i, date in enumerate(headers[1:], 1):
                status = student_rows[0][i] if i < len(student_rows[0]) else "N/A"
                report += f"  {date}: {status}\n"
        else:
            report = "Full attendance report:\n"
            report += " | ".join(headers) + "\n"
            report += "-" * 50 + "\n"
            for row in rows:
                report += " | ".join(row) + "\n"

        return report
    except Exception as e:
        return f"Attendance report failed: {str(e)}"