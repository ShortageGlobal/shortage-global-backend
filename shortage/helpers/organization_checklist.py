from functools import reduce
from rest_framework.exceptions import ValidationError


class Remark:
    SEVERITY_WARNING = "WARNING"
    SEVERITY_ERROR = "ERROR"

    @staticmethod
    def make(code=None, message=None, severity=None):
        return {
            "code": code,
            "message": message,
            "severity": severity,
        }


def get_organization_checklist(organization=None):
    """Check prerequisites for organization publication"""

    if organization is None:
        raise ValidationError("Organization is not provided")

    # form a list of remarks grouped by categories
    checklist = {
        "page": get_nonprofit_page_remarks(organization),
        "products": get_products_remarks(organization),
        "instructions": get_instructions_remarks(organization),
        "tax_information": get_tax_information_remarks(organization),
    }

    # can publish if there are no remarks with errors
    can_publish = all(
        remark["severity"] != Remark.SEVERITY_ERROR
        for remark in reduce(lambda acc, val: acc + val, checklist.values())
    )

    return {
        "checklist": checklist,
        "can_publish": can_publish,
    }


def get_nonprofit_page_remarks(organization):
    result = []
    # no requested goods field
    if not bool(organization.requested_goods):
        result.append(
            Remark.make(
                code="empty_requested_goods",
                message='"Support with" field is empty.',
                severity=Remark.SEVERITY_ERROR,
            )
        )
    # no logo
    if not bool(organization.logo):
        result.append(
            Remark.make(
                code="empty_logo",
                message="Logo is empty.",
                severity=Remark.SEVERITY_WARNING,
            )
        )
    # no banner
    if not bool(organization.banner):
        result.append(
            Remark.make(
                code="empty_banner",
                message="Banner is empty.",
                severity=Remark.SEVERITY_WARNING,
            )
        )
    return result


def get_products_remarks(organization):
    result = []
    # no active products
    if not organization.products.active():
        result.append(
            Remark.make(
                code="empty_products",
                message="There must be at least one item requested by your organization.",
                severity=Remark.SEVERITY_ERROR,
            )
        )
    return result


def get_instructions_remarks(organization):
    instructions = organization.instructions.all()
    result = []

    # no instructions
    if not instructions:
        result.append(
            Remark.make(
                code="no_instructions",
                message="Delivery instructions are not provided. Donors must know where to send goods.",
                severity=Remark.SEVERITY_ERROR,
            )
        )
        return result

    instruction = instructions[0]

    # no address_line1
    if not bool(instruction.address_line1):
        result.append(
            Remark.make(
                code="empty_instruction_address",
                message="Address Line 1 is empty.",
                severity=Remark.SEVERITY_ERROR,
            )
        )
    # no city
    if not bool(instruction.city):
        result.append(
            Remark.make(
                code="empty_instruction_city",
                message="City is empty.",
                severity=Remark.SEVERITY_ERROR,
            )
        )
    # no state_province_region
    if not bool(instruction.state_province_region):
        result.append(
            Remark.make(
                code="empty_instruction_state_province_region",
                message="State / Province.",
                severity=Remark.SEVERITY_ERROR,
            )
        )
    # no zip
    if not bool(instruction.zip):
        result.append(
            Remark.make(
                code="empty_instruction_zip",
                message="ZIP is empty.",
                severity=Remark.SEVERITY_ERROR,
            )
        )
    return result


def get_tax_information_remarks(organization):
    result = []
    # no automatic tax deduction receipt generation
    if not organization.can_generate_tax_receipts():
        result.append(
            Remark.make(
                code="empty_tax_information",
                message="Tax information is not sufficient. Until you provide correct EIN number, address, etc. we won't be able to automatically generate tax deduction receipts for you. You are still able to upload tax receipts yourself.",
                severity=Remark.SEVERITY_WARNING,
            )
        )
    return result
