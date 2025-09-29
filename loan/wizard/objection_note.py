from odoo import models, fields, api

class LoanNoteWizard(models.TransientModel):
    _name = 'loan.note.wizard'
    _description = 'Loan Note Wizard'

    note = fields.Text(string="Note")
    confirmed = fields.Boolean(string="Confirmed", default=False)

    def confirm_note_action(self):
        # Find the active loan record
        loan_id = self.env.context.get('active_id')
        if loan_id:
            loan_record = self.env['loan.order'].browse(loan_id)
            # Post the note to the chatter
            loan_record.message_post(body=self.note)

        # Mark the note as confirmed
        self.confirmed = True
        return {'type': 'ir.actions.act_window_close'}