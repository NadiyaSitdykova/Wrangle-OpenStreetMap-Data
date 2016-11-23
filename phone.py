import xml.etree.cElementTree as ET
import re

formatted_phone_re = re.compile(r'(\+996\s[0-9]{3}\s[0-9]{6}(;\s)?)+$')
valid_phone_digits_re = re.compile(r'(996|0|9960|0996)?([0-9]{3})?[0-9]{6}$')

# Takes string with formatted phone number and removes all symboles except digits
def leave_only_digits(phone):
    phone_digits = ""
    for symbol in phone:
        if symbol.isdigit():
            phone_digits += symbol
    return phone_digits

# Takes a single phone number and returns it in standard format as described
# in ttps://wiki.openstreetmap.org/wiki/Key:phone, if it's a valid phone number.
# Otherwise returns None
def fix_format(phone):
    phone_digits = leave_only_digits(phone)

    # process short codes
    if len(phone_digits) == 3:
        return phone_digits

    if not valid_phone_digits_re.match(phone_digits):
        return None

    if len(phone_digits) == 6:
        phone_digits = "996312" + phone_digits
    if len(phone_digits) == 9:
        phone_digits = "996" + phone_digits
    if len(phone_digits) == 10 and phone_digits[0] == "0":
        phone_digits = "996" + phone_digits[1:]
    if len(phone_digits) == 13:
        if phone_digits[0] == "0":
            phone_digits = phone_digits[1:]
        if phone_digits[:4] == "9960":
            phone_digits = "996" + phone_digits[4:]

    #add plus and spaces for standard formatting
    fixed_phone = "+" + phone_digits[:3] + " " + phone_digits[3:6] + " " + phone_digits[6:]
    return fixed_phone

def audit_phone(filename):
    unexpected_phones = []
    with open(filename, 'r') as file:
        for _, elem in ET.iterparse(file, events=("start",)):
            if elem.tag == "node" or elem.tag == "way":
                for tag in elem.iter("tag"):
                    if tag.attrib['k'] == "phone":
                        phone = tag.attrib['v']
                        if not formatted_phone_re.match:
                            unexpected_phones.append(phone)
    return unexpected_phones

def clean_phone(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    for child in root:
        if child.tag == "node" or child.tag == "way":
            for tag in child.iter("tag"):
                if tag.attrib['k'] == "phone":
                    raw_phone = tag.attrib['v']
                    #if there is more than one phone number
                    phones = raw_phone.split(";")
                    if len(phones) == 1:
                        phones = raw_phone.split(",")
                    #monkey patch
                    if raw_phone == "0(312)88-14-14 0(556)11-22-33":
                        phones = raw_phone.split(" ")
                    fixed_phones = []
                    for phone in phones:
                        fixed_phones.append(fix_format(phone))
                    if len(fixed_phones) == 1:
                        fixed_phone = fixed_phones[0]
                        if fixed_phone == None:
                            child.remove(tag)
                        else:
                            tag.attrib['v'] = fixed_phone
                    else:
                        fixed_phone = ""
                        for phone in fixed_phones:
                            if phone != None:
                                fixed_phone += phone + "; "
                        fixed_phone = fixed_phone[:-2]
                        tag.attrib['v'] = fixed_phone

    tree.write("cleaned_phone_" + filename, encoding='utf-8')