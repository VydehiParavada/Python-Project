from django import forms
from django.core.exceptions import ValidationError
import re

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Submit, Reset #Div, HTML 

from .models import Product, Customer

# v2.1 Added Customer Form.
# A nice tutorial on Crispy Forms is at: https://simpleisbetterthancomplex.com/tutorial/2018/11/28/advanced-form-rendering-with-django-crispy-forms.html
class CustomerForm(forms.ModelForm):
    
    
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
            Row(
                Column('customer_name', css_class='form-group col-6'),
                Column('contact_name', css_class='form-group col-6'),
                css_class='form-row'
            ),
            'address',
            Row(
                Column('city', css_class='form-group col-6'),
                Column('postal_code', css_class='form-group col-3'),
                Column('country', css_class='form-group col-3'),
                css_class='form-row'
            ),
           
            Submit('submit','Add Customer',
                   css_class='btn btn-light mt-3',
            ) 
            
                 
        )

    class Meta:
        model = Customer
        # can have additional fields on this line.
        fields = ("customer_name", 'contact_name', 'address', 'city', 'postal_code', 'country')
        
    def clean_customer_name(self):
        customer_name = self.cleaned_data.get('customer_name')
        if not customer_name:
            raise ValidationError("This field is required.")
        if len(customer_name) < 3:
            raise ValidationError("Customer Name must be at least 3 characters long.")
        if re.search(r'\d', customer_name):
            raise ValidationError("Customer Name cannot contain numbers.")
        return customer_name

    def clean_contact_name(self):
        contact_name = self.cleaned_data.get('contact_name')
        if not contact_name:
            raise ValidationError("Contact Name cannot be empty.")
        if len(contact_name) < 3:
            raise ValidationError("Contact Name must be at least 3 characters long.")
        if re.search(r'\d', contact_name):
            raise ValidationError("Customer Name cannot contain numbers.")
        return contact_name

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address:
            raise ValidationError("Address cannot be empty.")
        
        return address

    def clean_city(self):
        city = self.cleaned_data.get('city')
        if not city:
            raise ValidationError("City cannot be empty.")
        if len(city) < 3:
            raise ValidationError("City must be at least 3 characters long.")
        return city

    def clean_postal_code(self):
        postal_code = self.cleaned_data.get('postal_code')
        if not postal_code:
            raise ValidationError("Postal Code cannot be empty.")
        if len(postal_code) != 5 or not re.match(r'^\d{5}$', postal_code):
            raise ValidationError("Postal Code must be exactly 5 digits.")
        return postal_code

    def clean_country(self):
        country = self.cleaned_data.get('country')
        if not country:
            raise ValidationError("Country cannot be empty.")
        if re.search(r'\d', country):
            raise ValidationError("Country cannot contain numbers.")
        if len(country) < 2:
            raise ValidationError("Country must be at least 2 characters long.")
        return country
        

class ProductForm(forms.ModelForm):
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper(self)
        self.helper.layout = Layout(
           
            Reset('reset', 'formreset', css_class='btn btn-secondary')      
        )
    
    class Meta:
        model = Product
        fields = ("product_name", 'price', 'category', 'unit')
         
    
    def clean_price(self):
        price = self.cleaned_data.get('price') 
    
        if price is None or price == '':
            raise ValidationError("Product Price cannot be empty.")
    
        if price < 0:
            raise ValidationError("Product Price cannot be negative.")
    
        elif price > 500:
            raise ValidationError("Product Price is never more than $800.00")
    
        return price 
    
    def clean_product_name(self):
        product_name = self.cleaned_data.get('product_name')
        
        if not product_name:
            raise ValidationError("Product Name cannot be empty.")

        if len(product_name) < 2:
            raise ValidationError("Product Name must be at least 2 characters long.")
           
        if re.search(r'\d', product_name):
            raise ValidationError("Product Name cannot contain numbers.")
        
        return product_name
    
    def clean_unit(self):
        unit = self.cleaned_data.get('unit')
        
        if not unit:
            raise ValidationError("Unit cannot be empty.")
        
        if unit == "0":
            raise ValidationError("Unit cannot be Zero.")
        
        
        return unit
    

    
   
    
    
    

            
        
  
  
