from api_helper import CubeApiPy
import global_settings
import utils
import logging_include
from datetime import datetime, date
import datetime



cube = None

def tradejini_response_validation(tradejini_response):

    func_called_from = "tradejini_response_validation"
    
    try:

        err = ''
        validation_success = False

        if type(tradejini_response) is dict: 
            if tradejini_response['stat'] == 'Ok':
                validation_success = True
                
            else:
                err = tradejini_response['emsg']
        else:
            err = "Invalid response from Tradejini.."
        
        return(validation_success, err)

    except Exception as e:
        logging_include.log_exception(e, func_called_from, exit_required=False)


def tradejini_init():
    
    func_called_from = "tradejini_init"
    
    try:
        global cube
        #start of our program
        cube = CubeApiPy()

        token_from_kvstore = utils.get_set_token_from_kvstore("get_token", global_settings.cube_user)

        #use the token and see if its valid.. if its invalid, tradejini will respond with susertoken. Store that
        tradejini_response = cube.set_session(userid= global_settings.cube_user, password = global_settings.cube_pwd, usertoken= token_from_kvstore)
        #check if its valid by trying to get limits
        get_limits = cube.get_limits()

        '''
        {'stat': 'Not_Ok', 'emsg': 'Session Expired :  Invalid Session Key'}
        {'request_time': '23:14:11 15-09-2022', 'stat': 'Ok', 'prfname': 'ONLINE25', 'cash': '0.00', 'payin': '0.00', 'payout': '0.00', 'brkcollamt': '0.00', 'unclearedcash': '0.00', 'aux_daycash': '0.00', 'aux_brkcollamt': '0.00', 'aux_unclearedcash': '0.00', 'daycash': '0.00', 'turnoverlmt': '50000000000.00', 'pendordvallmt': '50000000000.00'}
        '''

        tradejini_get_limits_response_successful, get_limit_err_msg = tradejini_response_validation(get_limits)

        if not tradejini_get_limits_response_successful:
            
            #session is stale.. Login using id, pwd and store the token
            tradejini_login_response = cube.login(userid=global_settings.cube_user, password=global_settings.cube_pwd, twoFA=global_settings.cube_factor2, vendor_code=global_settings.cube_vc, api_secret=global_settings.cube_app_key, imei='abc12453')

            tradejini_login_response_successful, login_resp_err_msg = tradejini_response_validation(tradejini_login_response)

            if not tradejini_login_response_successful:
                login_resp_err_msg = "Tradejini Login issue - " + login_resp_err_msg
                logging_include.log_exception(login_resp_err_msg, func_called_from, exit_required=False)
                
            else:
                #set the token back to kvstore so that it can be used in other programs
                utils.get_set_token_from_kvstore("update_token", global_settings.cube_user, data=tradejini_login_response['susertoken'])
        
        return
    
    except Exception as e:
        logging_include.log_exception(e, func_called_from, False)


def tradejini_get_ltp(market, token):

    func_called_from = "tradejini_get_ltp"
    
    try:
        all_set_to_retrieve_ltp = False
        ltp = 0.0

        for retry in range(0,2):
            
            ltp_response = cube.get_quotes(exchange=market, token=str(token))
            tradejini_ltp_response_successful, ltp_err_msg = tradejini_response_validation(ltp_response)
            
            if (tradejini_ltp_response_successful) and ('lp' in ltp_response):
                all_set_to_retrieve_ltp = True
                break
            else:
                logging_include.log_exception("ltp exception - " + ltp_err_msg, func_called_from, exit_required=False)
                #retry once more before giving up

        if all_set_to_retrieve_ltp:
            ltp = ltp_response['lp']
        
        else:
            logging_include.log_exception("ltp exception - " + ltp_err_msg, func_called_from, exit_required=False)
        
        return(ltp)

    except Exception as e:
        logging_include.log_exception(e, func_called_from, False)


def tradejini_get_historical_data(market, token, start_time, end_time, interval):
    
    func_called_from = "tradejini_get_historical_data"
    
    try:

        hist_data = cube.get_time_price_series(exchange=market, token=token, starttime=start_time.timestamp(), endtime=end_time.timestamp(), interval=interval)
        return(hist_data)

    except Exception as e:
        logging_include.log_exception(e, func_called_from, False)
