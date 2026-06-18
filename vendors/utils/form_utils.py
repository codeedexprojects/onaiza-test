from main.functions import get_auto_id, generate_form_errors


class FormUtils:
    def __init__(self, request, form, model):
        self.request = request
        self.form = form
        self.model = model

    def save_form_data_to_model(self, form):
        auto_id = get_auto_id(self.model)

        data = form.save(commit=False)
        data.creator = self.request.user
        data.updater = self.request.user
        data.auto_id = auto_id

        data.vendor_created = True
        data.is_admin_approved = None

        data.save()

        return data.pk

    def save_form_data(self):
        response_data = {}

        form = self.form(self.request.POST, self.request.FILES)
        if form.is_valid():
            saved_datas = self.save_form_data_to_model(form)

            response_data['status'] = True
            response_data['pk'] = saved_datas
        else:
            message = generate_form_errors(form, formset=False)
            response_data['status'] = False
            response_data['message'] = message

        return response_data
