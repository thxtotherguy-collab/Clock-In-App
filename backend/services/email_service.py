"""
Email Service - MOCKED implementation.
Builds professional HTML email templates and logs instead of sending.
Designed for easy swap to SendGrid, SMTP, or any real provider.

To switch to a real provider:
1. Set EMAIL_PROVIDER env var (e.g., "sendgrid", "smtp")
2. Set required credentials (SENDGRID_API_KEY or SMTP_* vars)
3. Replace the _send_email method
"""
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.base import generate_uuid, utc_now

logger = logging.getLogger("email_service")


class EmailService:
    """Email service with MOCKED sending. All emails are logged to DB."""

    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self.provider = os.environ.get("EMAIL_PROVIDER", "mock")
        self.from_email = os.environ.get("EMAIL_FROM", "reports@workforce-mgmt.com")
        self.from_name = os.environ.get("EMAIL_FROM_NAME", "Workforce Management")

    async def send_daily_report(
        self,
        report_data: Dict,
        recipients: List[str],
        cc: List[str] = None,
        branch_name: str = "All Branches"
    ) -> Dict:
        """
        Send daily attendance report email.
        Returns send result with status.
        """
        subject = f"Daily Attendance Report - {branch_name} - {report_data.get('report_date', 'Today')}"

        html_content = self._build_daily_report_html(report_data, branch_name)

        result = await self._send_email(
            to=recipients,
            cc=cc or [],
            subject=subject,
            html_body=html_content,
            report_type="daily_attendance",
            metadata={
                "report_date": report_data.get("report_date"),
                "branch_name": branch_name,
                "summary": report_data.get("summary", {})
            }
        )

        return result

    async def send_payroll_summary(
        self,
        payroll_data: Dict,
        recipients: List[str],
        cc: List[str] = None
    ) -> Dict:
        """Send payroll summary email."""
        period = payroll_data.get("period", {})
        subject = f"Payroll Summary - {period.get('start', '')} to {period.get('end', '')}"

        html_content = self._build_payroll_html(payroll_data)

        return await self._send_email(
            to=recipients,
            cc=cc or [],
            subject=subject,
            html_body=html_content,
            report_type="payroll_summary",
            metadata={"period": period, "totals": payroll_data.get("totals", {})}
        )

    async def _send_email(
        self,
        to: List[str],
        cc: List[str],
        subject: str,
        html_body: str,
        report_type: str,
        metadata: Dict = None
    ) -> Dict:
        """
        Send email - MOCKED. Logs to database and console.
        Replace this method to integrate real email provider.
        """
        now = utc_now()
        email_record = {
            "id": generate_uuid(),
            "to": to,
            "cc": cc,
            "from_email": self.from_email,
            "from_name": self.from_name,
            "subject": subject,
            "html_body": html_body,
            "report_type": report_type,
            "metadata": metadata or {},
            "provider": self.provider,
            "status": "sent" if self.provider != "mock" else "mocked",
            "sent_at": now.isoformat(),
            "created_at": now.isoformat()
        }

        # Log to database
        await self.db.email_logs.insert_one(email_record)
        email_record.pop("_id", None)

        # Log to console
        logger.info(
            f"[EMAIL {'MOCKED' if self.provider == 'mock' else 'SENT'}] "
            f"To: {', '.join(to)} | CC: {', '.join(cc)} | "
            f"Subject: {subject} | Type: {report_type}"
        )

        if self.provider == "mock":
            logger.info(
                f"[EMAIL MOCK] Email logged to DB (id: {email_record['id']}). "
                f"To send real emails, set EMAIL_PROVIDER env var."
            )

        return {
            "id": email_record["id"],
            "status": email_record["status"],
            "recipients": to,
            "cc": cc,
            "subject": subject,
            "sent_at": email_record["sent_at"]
        }

    def _build_daily_report_html(self, data: Dict, branch_name: str) -> str:
        """Build professional HTML email for daily attendance report."""
        summary = data.get("summary", {})
        report_date = data.get("report_date", "")

        # Worker hours rows
        worker_rows = ""
        for w in data.get("worker_hours", [])[:50]:  # Cap at 50
            ot_badge = f'<span style="background:#FEF3C7;color:#92400E;padding:2px 6px;border-radius:4px;font-size:11px;">{w.get("overtime_hours", 0)}h OT</span>' if w.get("overtime_hours", 0) > 0 else ""
            worker_rows += f"""
            <tr style="border-bottom:1px solid #E5E7EB;">
                <td style="padding:10px 12px;font-size:13px;color:#374151;">{w.get('employee_id','')}</td>
                <td style="padding:10px 12px;font-size:13px;color:#111827;font-weight:500;">{w.get('name','')}</td>
                <td style="padding:10px 12px;font-size:13px;color:#6B7280;">{w.get('branch','')}</td>
                <td style="padding:10px 12px;font-size:13px;color:#111827;font-weight:600;text-align:right;">{w.get('hours',0)}h</td>
                <td style="padding:10px 12px;text-align:right;">{ot_badge}</td>
            </tr>"""

        # Late arrivals rows
        late_rows = ""
        for la in data.get("late_arrivals", []):
            ci_time = ""
            if la.get("clock_in"):
                try:
                    ci_time = datetime.fromisoformat(la["clock_in"].replace("Z", "+00:00")).strftime("%H:%M")
                except (ValueError, AttributeError):
                    ci_time = str(la["clock_in"])[:5]
            late_rows += f"""
            <tr style="border-bottom:1px solid #FDE8E8;">
                <td style="padding:8px 12px;font-size:13px;color:#374151;">{la.get('name','')}</td>
                <td style="padding:8px 12px;font-size:13px;color:#374151;">{la.get('branch','')}</td>
                <td style="padding:8px 12px;font-size:13px;color:#DC2626;font-weight:500;">{ci_time}</td>
            </tr>"""

        # Absentee rows
        absent_rows = ""
        for ab in data.get("absentees", []):
            absent_rows += f"""
            <tr style="border-bottom:1px solid #FDE8E8;">
                <td style="padding:8px 12px;font-size:13px;color:#374151;">{ab.get('employee_id','')}</td>
                <td style="padding:8px 12px;font-size:13px;color:#374151;">{ab.get('name','')}</td>
                <td style="padding:8px 12px;font-size:13px;color:#6B7280;">{ab.get('branch','')}</td>
            </tr>"""

        # Branch breakdown rows
        branch_rows = ""
        for bb in data.get("branch_breakdown", []):
            branch_rows += f"""
            <tr style="border-bottom:1px solid #E5E7EB;">
                <td style="padding:10px 12px;font-size:13px;color:#111827;font-weight:500;">{bb.get('branch_name','')}</td>
                <td style="padding:10px 12px;font-size:13px;color:#111827;text-align:right;">{bb.get('workers_count',0)}</td>
                <td style="padding:10px 12px;font-size:13px;color:#111827;text-align:right;font-weight:600;">{bb.get('total_hours',0)}h</td>
                <td style="padding:10px 12px;font-size:13px;color:#D97706;text-align:right;">{bb.get('overtime_hours',0)}h</td>
                <td style="padding:10px 12px;font-size:13px;color:#DC2626;text-align:right;">{bb.get('late_count',0)}</td>
                <td style="padding:10px 12px;font-size:13px;color:#DC2626;text-align:right;">{bb.get('absent_count',0)}</td>
            </tr>"""

        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#F3F4F6;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;margin:0 auto;background:#FFFFFF;">

  <!-- Header -->
  <tr>
    <td style="background:linear-gradient(135deg,#1E3A5F 0%,#2563EB 100%);padding:28px 32px;">
      <h1 style="margin:0;color:#FFFFFF;font-size:22px;font-weight:700;">Daily Attendance Report</h1>
      <p style="margin:6px 0 0;color:#93C5FD;font-size:14px;">{branch_name} &mdash; {report_date}</p>
    </td>
  </tr>

  <!-- Summary Cards -->
  <tr>
    <td style="padding:24px 32px 16px;">
      <table width="100%" cellpadding="0" cellspacing="8">
        <tr>
          <td style="background:#EFF6FF;border-radius:10px;padding:16px;text-align:center;width:25%;">
            <div style="font-size:28px;font-weight:700;color:#1D4ED8;">{summary.get('clocked_in', 0)}</div>
            <div style="font-size:11px;color:#6B7280;margin-top:4px;text-transform:uppercase;letter-spacing:0.5px;">Clocked In</div>
          </td>
          <td style="background:#FEF3C7;border-radius:10px;padding:16px;text-align:center;width:25%;">
            <div style="font-size:28px;font-weight:700;color:#92400E;">{summary.get('late_arrivals', 0)}</div>
            <div style="font-size:11px;color:#6B7280;margin-top:4px;text-transform:uppercase;letter-spacing:0.5px;">Late Arrivals</div>
          </td>
          <td style="background:#FEE2E2;border-radius:10px;padding:16px;text-align:center;width:25%;">
            <div style="font-size:28px;font-weight:700;color:#DC2626;">{summary.get('absentees', 0)}</div>
            <div style="font-size:11px;color:#6B7280;margin-top:4px;text-transform:uppercase;letter-spacing:0.5px;">Absent</div>
          </td>
          <td style="background:#F0FDF4;border-radius:10px;padding:16px;text-align:center;width:25%;">
            <div style="font-size:28px;font-weight:700;color:#166534;">{summary.get('total_hours', 0)}h</div>
            <div style="font-size:11px;color:#6B7280;margin-top:4px;text-transform:uppercase;letter-spacing:0.5px;">Total Hours</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Extra Stats Row -->
  <tr>
    <td style="padding:0 32px 20px;">
      <table width="100%" cellpadding="0" cellspacing="8">
        <tr>
          <td style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px 16px;text-align:center;width:33%;">
            <span style="font-size:18px;font-weight:700;color:#374151;">{summary.get('total_workers', 0)}</span>
            <span style="font-size:12px;color:#9CA3AF;margin-left:6px;">Total Workers</span>
          </td>
          <td style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px 16px;text-align:center;width:33%;">
            <span style="font-size:18px;font-weight:700;color:#D97706;">{summary.get('total_overtime', 0)}h</span>
            <span style="font-size:12px;color:#9CA3AF;margin-left:6px;">Total Overtime</span>
          </td>
          <td style="background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:12px 16px;text-align:center;width:33%;">
            <span style="font-size:18px;font-weight:700;color:#059669;">{summary.get('still_working', 0)}</span>
            <span style="font-size:12px;color:#9CA3AF;margin-left:6px;">Still Working</span>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <!-- Branch Breakdown -->
  {f'''
  <tr>
    <td style="padding:0 32px 24px;">
      <h2 style="font-size:15px;color:#1F2937;margin:0 0 12px;font-weight:600;">Hours by Branch</h2>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;">
        <tr style="background:#F9FAFB;">
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Branch</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Workers</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Hours</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Overtime</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Late</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Absent</th>
        </tr>
        {branch_rows}
      </table>
    </td>
  </tr>
  ''' if branch_rows else ''}

  <!-- Worker Hours -->
  <tr>
    <td style="padding:0 32px 24px;">
      <h2 style="font-size:15px;color:#1F2937;margin:0 0 12px;font-weight:600;">Hours per Worker</h2>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;">
        <tr style="background:#F9FAFB;">
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">ID</th>
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Name</th>
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Branch</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Hours</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">OT</th>
        </tr>
        {worker_rows if worker_rows else '<tr><td colspan="5" style="padding:20px;text-align:center;color:#9CA3AF;">No workers clocked in today</td></tr>'}
      </table>
    </td>
  </tr>

  <!-- Late Arrivals -->
  {f'''
  <tr>
    <td style="padding:0 32px 24px;">
      <h2 style="font-size:15px;color:#DC2626;margin:0 0 12px;font-weight:600;">&#9888; Late Arrivals ({len(data.get('late_arrivals', []))})</h2>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #FDE8E8;border-radius:8px;overflow:hidden;background:#FFF5F5;">
        <tr style="background:#FEE2E2;">
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#991B1B;font-weight:600;">Name</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#991B1B;font-weight:600;">Branch</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#991B1B;font-weight:600;">Clock In</th>
        </tr>
        {late_rows}
      </table>
    </td>
  </tr>
  ''' if late_rows else ''}

  <!-- Absentees -->
  {f'''
  <tr>
    <td style="padding:0 32px 24px;">
      <h2 style="font-size:15px;color:#DC2626;margin:0 0 12px;font-weight:600;">&#10060; Absentees ({len(data.get('absentees', []))})</h2>
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #FDE8E8;border-radius:8px;overflow:hidden;background:#FFF5F5;">
        <tr style="background:#FEE2E2;">
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#991B1B;font-weight:600;">ID</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#991B1B;font-weight:600;">Name</th>
          <th style="padding:8px 12px;text-align:left;font-size:11px;color:#991B1B;font-weight:600;">Branch</th>
        </tr>
        {absent_rows}
      </table>
    </td>
  </tr>
  ''' if absent_rows else ''}

  <!-- Footer -->
  <tr>
    <td style="padding:24px 32px;background:#F9FAFB;border-top:1px solid #E5E7EB;">
      <p style="margin:0;font-size:12px;color:#9CA3AF;text-align:center;">
        This report was auto-generated by Workforce Management System<br>
        Generated at {data.get('generated_at', '')[:19]} UTC
      </p>
    </td>
  </tr>

</table>
</body>
</html>"""
        return html

    def _build_payroll_html(self, data: Dict) -> str:
        """Build professional HTML email for payroll summary."""
        period = data.get("period", {})
        totals = data.get("totals", {})

        employee_rows = ""
        for emp in data.get("employees", [])[:100]:
            employee_rows += f"""
            <tr style="border-bottom:1px solid #E5E7EB;">
                <td style="padding:8px 12px;font-size:12px;color:#374151;">{emp.get('employee_id','')}</td>
                <td style="padding:8px 12px;font-size:12px;color:#111827;font-weight:500;">{emp.get('name','')}</td>
                <td style="padding:8px 12px;font-size:12px;color:#6B7280;">{emp.get('branch_name','')}</td>
                <td style="padding:8px 12px;font-size:12px;text-align:right;">{emp.get('days_worked',0)}</td>
                <td style="padding:8px 12px;font-size:12px;text-align:right;font-weight:500;">{emp.get('regular_hours',0)}h</td>
                <td style="padding:8px 12px;font-size:12px;text-align:right;color:#D97706;font-weight:500;">{emp.get('overtime_hours',0)}h</td>
                <td style="padding:8px 12px;font-size:12px;text-align:right;font-weight:700;">{emp.get('total_hours',0)}h</td>
            </tr>"""

        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="margin:0;padding:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#F3F4F6;">
<table width="100%" cellpadding="0" cellspacing="0" style="max-width:700px;margin:0 auto;background:#FFFFFF;">

  <tr>
    <td style="background:linear-gradient(135deg,#064E3B 0%,#059669 100%);padding:28px 32px;">
      <h1 style="margin:0;color:#FFFFFF;font-size:22px;font-weight:700;">Payroll Summary</h1>
      <p style="margin:6px 0 0;color:#A7F3D0;font-size:14px;">Pay Period: {period.get('start','')} to {period.get('end','')}</p>
    </td>
  </tr>

  <tr>
    <td style="padding:24px 32px 16px;">
      <table width="100%" cellpadding="0" cellspacing="8">
        <tr>
          <td style="background:#F0FDF4;border-radius:10px;padding:16px;text-align:center;width:25%;">
            <div style="font-size:28px;font-weight:700;color:#166534;">{totals.get('employee_count',0)}</div>
            <div style="font-size:11px;color:#6B7280;margin-top:4px;text-transform:uppercase;">Employees</div>
          </td>
          <td style="background:#EFF6FF;border-radius:10px;padding:16px;text-align:center;width:25%;">
            <div style="font-size:28px;font-weight:700;color:#1D4ED8;">{totals.get('total_regular_hours',0)}h</div>
            <div style="font-size:11px;color:#6B7280;margin-top:4px;text-transform:uppercase;">Regular Hours</div>
          </td>
          <td style="background:#FEF3C7;border-radius:10px;padding:16px;text-align:center;width:25%;">
            <div style="font-size:28px;font-weight:700;color:#92400E;">{totals.get('total_overtime_hours',0)}h</div>
            <div style="font-size:11px;color:#6B7280;margin-top:4px;text-transform:uppercase;">Overtime</div>
          </td>
          <td style="background:#F0FDF4;border-radius:10px;padding:16px;text-align:center;width:25%;">
            <div style="font-size:28px;font-weight:700;color:#166534;">{totals.get('total_hours',0)}h</div>
            <div style="font-size:11px;color:#6B7280;margin-top:4px;text-transform:uppercase;">Total Hours</div>
          </td>
        </tr>
      </table>
    </td>
  </tr>

  <tr>
    <td style="padding:0 32px 24px;">
      <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #E5E7EB;border-radius:8px;overflow:hidden;">
        <tr style="background:#F9FAFB;">
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">ID</th>
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Name</th>
          <th style="padding:10px 12px;text-align:left;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Branch</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Days</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Regular</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">OT</th>
          <th style="padding:10px 12px;text-align:right;font-size:11px;color:#6B7280;font-weight:600;text-transform:uppercase;">Total</th>
        </tr>
        {employee_rows if employee_rows else '<tr><td colspan="7" style="padding:20px;text-align:center;color:#9CA3AF;">No data for this period</td></tr>'}
      </table>
    </td>
  </tr>

  <tr>
    <td style="padding:16px 32px;background:#F0FDF4;border-top:2px solid #059669;">
      <p style="margin:0;font-size:13px;color:#374151;">
        <strong>SA BCEA Overtime:</strong> 1.5x after 9hrs/day (5-day week) or 8hrs/day (6-day week) &bull;
        Weekly threshold: 45hrs &bull; Max OT: 10hrs/week &bull;
        Sunday/Public Holiday: 2x rate
      </p>
    </td>
  </tr>

  <tr>
    <td style="padding:24px 32px;background:#F9FAFB;border-top:1px solid #E5E7EB;">
      <p style="margin:0;font-size:12px;color:#9CA3AF;text-align:center;">
        Generated by Workforce Management System &bull; {data.get('generated_at','')[:19]} UTC
      </p>
    </td>
  </tr>

</table>
</body>
</html>"""
        return html
