import base64
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView
from django.views.generic.detail import DetailView

#from baseapp.decorators import admin_required
from itemmanager.models.item import Item
from itemmanager.models.restockitem import RestockItem
from itemmanager.forms import ItemForm

import math

import qrcode
from io import BytesIO



def generate_qr_code(self, item):
    # Create a QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    
    # Add data to the QR code (you can customize this data as per your item details)
    qr.add_data(f"Item: {item.item_name}\nPrice: ${item.price}")

    # Make the QR code image
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # Save the QR code image to a BytesIO buffer
    buffer = BytesIO()
    qr_img.save(buffer, format="PNG")

    return buffer




class PricelistView(TemplateView):
    model = Item
    template_name = 'pricelist.html'

    def get_context_data(self, *args, **kwargs):
        filter_pattern = kwargs.get('filter')
        pagination = kwargs.get('page')
        try:
            pagination = int(pagination) - 1
        except ValueError:
            pagination = 0
        pagination = pagination if pagination > 0 else 0
        item_per_page = 10
        items = Item.objects.order_by('item_name').filter(item_name__icontains=filter_pattern)
        max_pagination = math.ceil(items.count() / item_per_page)
        min_item_index = pagination*item_per_page
        context = {
            'items': items[min_item_index:min_item_index+item_per_page],
            'paginations': range(1, max_pagination+1),
            'pagination': pagination + 1,
            'min_item_index': min_item_index,
            'filter_pattern': filter_pattern,
            'active_tab': 'item'
        }
        return context

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        filter_pattern = request.GET.get('f', '') or ''
        pagination = request.GET.get('p', '') or 1
        context = self.get_context_data(filter=filter_pattern, page=pagination)
        return render(request, self.template_name, context)


class ItemDetailView(TemplateView):
    model = Item
    template_name = 'item_detail.html'

    def generate_qr_code(self, item):
        # Create a QR code instance
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )



        # Make the QR code image
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")

        # Save the QR code image to a BytesIO buffer
        buffer = BytesIO()
        qr_img.save(buffer, format="PNG")

        return buffer

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=self.kwargs.get('pk'))
        context = self.get_context_data(item=item)

        # Generate the QR code for the specific item
        qr_code = self.generate_qr_code(item)
        qr_code_base64 = base64.b64encode(qr_code.getvalue()).decode('utf-8')
        qr_code.close()

        context['qr_code'] = qr_code_base64

        return render(request, self.template_name, context)



class ItemNewView(TemplateView):
    template_name = 'new_item.html'

    def post(self, request, *args, **kwargs):
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save()
            notice = "Item %s was successfully created" % item.item_name
            messages.success(request, notice, extra_tags='green rounded')
            return redirect('pricelist')
        else:
            # Handle form validation errors
            context = {'form': form}
            return render(request, self.template_name, context)

    def get(self, request, *args, **kwargs):
        form = ItemForm()
        context = {'form': form}
        return render(request, self.template_name, context)



class ItemEditView(TemplateView):
    model = Item
    template_name = 'item_edit.html'

    #@method_decorator(admin_required)
    def post(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=self.kwargs.get('pk'))
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            item = form.save(commit=False)
            item.save()
            notice = "Item %s was successfully changed" % item.item_name
            messages.success(request, notice, extra_tags='green rounded')
            return redirect('item_detail', pk=item.pk)
        else:
            context = {'form': form, 'active_tab': 'item'}
            return render(request, self.template_name, context)

    #
    def get(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=self.kwargs.get('pk'))
        form = ItemForm(instance=item)
        context = {'form': form, 'item_pk': item.pk, 'active_tab': 'item'}
        return render(request, self.template_name, context)


class ItemDeleteView(TemplateView):
    model = Item

    #
    def post(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=self.kwargs.get('pk'))
        notice = "Item %s was successfully deleted" % item.item_name
        item.delete()
        messages.success(request, notice, extra_tags='green rounded')
        return redirect('pricelist')

    #
    def get(self, request, *args, **kwargs):
        item = get_object_or_404(Item, pk=self.kwargs.get('pk'))
        return redirect('item_detail', pk=item.pk)
