"""Web RESTful API layer for automation."""
import inspect

from flask import jsonify
from flask import request
from uosinterface.hardware import UOSDevice
from uosinterface.webapp.api import API_VERSIONS
from uosinterface.webapp.api import blueprint
from uosinterface.webapp.api import util


@blueprint.route("<string:api_version>/<string:function>")
def route_hardware_function(api_version: str, function: str):
    """Can be used to execute standard UOS IO functions."""
    # todo first is to check the function exists
    arguments = inspect.signature(getattr(UOSDevice, function))
    possible_args = {
        argument.name: util.APIargument(
            argument.default == inspect.Parameter.empty, argument.annotation, None
        )
        for argument in arguments.parameters.values()
        if argument.name != "self"
    }
    response, required_args = util.check_required_args(
        possible_args, request.args, add_device=True
    )
    if response.status:
        device = UOSDevice(
            identity=required_args["identity"].arg_value,
            connection=required_args["connection"].arg_value,
        )
        if function in [
            function
            for function in dir(UOSDevice)
            if "get_" in function or "set_" in function
        ]:
            instr_response = getattr(device, function)(
                pin=required_args["pin"].arg_value,
                level=required_args["level"].arg_value,
            )
            response.status = instr_response.status
            response.com_data = instr_response
        else:  # dunno how to handle that function
            response.exception = f"function '{function}' has not been implemented."
            response.status = False
    return jsonify(response)
