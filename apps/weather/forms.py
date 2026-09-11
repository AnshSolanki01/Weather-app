"""
Django forms for the Weather App.
"""

from django import forms


class CitySearchForm(forms.Form):
    """Single-city search form with empty-input validation."""

    city = forms.CharField(
        label='City Name',
        max_length=120,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Search city…',
                'class': 'search-input',
                'autocomplete': 'off',
                'id': 'city-input',
                'role': 'combobox',
                'aria-autocomplete': 'list',
                'aria-expanded': 'false',
                'aria-controls': 'city-dropdown',
            }
        ),
        error_messages={
            'required': 'Please enter a city name.',
        },
    )

    def clean_city(self):
        """Strip whitespace and reject blank values."""
        city = self.cleaned_data.get('city', '').strip()
        if not city:
            raise forms.ValidationError('Please enter a city name.')
        return city


class CompareCitiesForm(forms.Form):
    """Form to compare weather between two cities."""

    city_a = forms.CharField(
        label='First City',
        max_length=120,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'First city…',
                'class': 'search-input',
                'autocomplete': 'off',
                'id': 'city-a-input',
            }
        ),
        error_messages={'required': 'Please enter the first city.'},
    )
    city_b = forms.CharField(
        label='Second City',
        max_length=120,
        required=True,
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Second city…',
                'class': 'search-input',
                'autocomplete': 'off',
                'id': 'city-b-input',
            }
        ),
        error_messages={'required': 'Please enter the second city.'},
    )

    def clean_city_a(self):
        city = self.cleaned_data.get('city_a', '').strip()
        if not city:
            raise forms.ValidationError('Please enter the first city.')
        return city

    def clean_city_b(self):
        city = self.cleaned_data.get('city_b', '').strip()
        if not city:
            raise forms.ValidationError('Please enter the second city.')
        return city

    def clean(self):
        cleaned = super().clean()
        city_a = cleaned.get('city_a', '')
        city_b = cleaned.get('city_b', '')
        if city_a and city_b and city_a.lower() == city_b.lower():
            raise forms.ValidationError('Please choose two different cities to compare.')
        return cleaned
