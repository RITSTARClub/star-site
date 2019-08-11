'use strict';
window.addEventListener('load', function () {
	var DEFAULT_MESSAGE = 'That URL does not look right.  Did you accidentally copy some extraneous parameters?',
		DEFAULT_MESSAGE_PLACEHOLDER = DEFAULT_MESSAGE + '  It should look like \u201c{{PLACEHOLDER}}\u201d.',
		MESSAGES = [
			{
				check: /^http:/,
				message: 'It looks like you have \u201chttp://\u201d instead of \u201chttps://\u201d.  Try changing that.'
			}, {
				check: /^(?!https:\/\/).+/,
				message: 'It looks like your URL is missing the \u201chttps://\u201d.  Try adding that.'
			}, {
				check: /\/a\/.+\.[A-Za-z]+\//,
				message: 'It looks like you might have a GSuite fragment in that link (e.g., \u201c/a/rit.edu/\u201d).  Try taking that out.'
			}, {
				check: /\/u\/[0-9]+\//,
				message: 'It looks like you might have a Google account fragment in that link (e.g., \u201c/u/1/\u201d).  Try taking that out.'
			}, {
				check: /\/b\/[0-9]+\//,
				message: 'It looks like you might have a Google brand account fragment in that link (e.g., \u201c/b/12345678890/\u201d).  Try taking that out.'
			}, {
				check: /(\?|&)(utm_|usp)/,
				message: 'It looks like you might have analytics tracking data in that link (e.g., \u201cutm...\u201d or \u201cusp...\u201d).  Try taking that out.'
			}
		];
	
	// Get type dependent fields.
	var weekNumberRow = document.getElementById('weekNumberRow'),
		carpoolStartRow = document.getElementById('carpoolStartRow'),
		carpoolEndRow = document.getElementById('carpoolEndRow'),
		carpoolLocationRow = document.getElementById('carpoolLocationRow');
	
	// Set up showing fields depending on the mission type.
	var typeSelect = document.getElementById('type');
	typeSelect.onchange = handleTypeChange;
	handleTypeChange.call(typeSelect);
	
	// Set up fields with custom format validation.
	var fieldsToValidate = document.querySelectorAll(
		'#wave_url,' +
		'#drive_url,' +
		'#intro_url,' +
		'#sign_in_url,' +
		'#fb_url,' +
		'#youtube_url,' +
		'#gplus_url,' +
		'#the_link_url');
	
	fieldsToValidate = Array.prototype.slice.call(fieldsToValidate);
	fieldsToValidate.forEach(function (field) {
		field.oninput = checkFieldValidation;
	});
	
	/**
	 * Show/hide fields when the mission type changes.
	 */
	function handleTypeChange() {
		// Only show the week number for weekly missions.
		weekNumberRow.style.display =
			(this.value === '0') ? null : 'none';
		
		// Only show carpool fields for away missions.
		carpoolStartRow.style.display =
			carpoolEndRow.style.display =
			carpoolLocationRow.style.display =
				(this.value === '2') ? null : 'none';
	}
	
	function checkFieldValidation() {
		// If there is no problem, then no message is needed.
		if (!this.validity || !(this.validity.typeMismatch || this.validity.patternMismatch)) {
			this.setCustomValidity('');
			return;
		}
		
		// Check prepared-for cases.
		for (var i = 0; i < MESSAGES.length; i++) {
			if (this.value.match(MESSAGES[i].check)) {
				this.setCustomValidity(MESSAGES[i].message);
				return;
			}
		}
		
		// Cite the placeholder if none of the prepared-for cases matched.
		if (this.placeholder) {
			this.setCustomValidity(DEFAULT_MESSAGE_PLACEHOLDER.replace('{{PLACEHOLDER}}', this.placeholder));
			return;
		}
		
		// Fall back to the default if nothing else.
		this.setCustomValidity(DEFAULT_MESSAGE);
	}
}, false);
