from test_common.util import Util


resp = Util.update_status('CDAF8A3D97D604DC516E353C694B857BFC65C02CD5A3B9A900F89F8ECFE1B86808FA380B73BE4D41933F61BF5D116EBD2E90D97B94FFD61E617920D5831B2E26', 'success', 'test-orchestrator', 'success')


print(resp)
print(resp.status_code)


