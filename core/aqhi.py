def cap(v):
    return None if v is None else ('10+' if v>10 else v)
def cap_str(v,d=0):
    if v is None:return 'unavailable'
    return '10+' if v>10 else f'{v:.{d}f}'
# Verbatim from Environment and Climate Change Canada, https://weather.gc.ca/airquality/healthmessage_e.html
ECCC_MESSAGES={
 'LOW':{'general':'Ideal air quality for outdoor activities.','at_risk':'Enjoy your usual outdoor activities.'},
 'MODERATE':{'general':'No need to modify your usual outdoor activities unless you experience symptoms such as coughing and throat irritation.','at_risk':'Consider reducing or rescheduling strenuous activities outdoors if you are experiencing symptoms.'},
 'HIGH':{'general':'Consider reducing or rescheduling strenuous activities outdoors if you experience symptoms such as coughing and throat irritation.','at_risk':'Reduce or reschedule strenuous activities outdoors. Children and the elderly should also take it easy.'},
 'EXTREME':{'general':'Reduce or reschedule strenuous activities outdoors, especially if you experience symptoms such as coughing and throat irritation.','at_risk':'Avoid strenuous activities outdoors. Children and the elderly should also avoid outdoor physical exertion.'},
}
def eccc_messages(risk):
    return ECCC_MESSAGES.get(risk)

def risk_from_aqhi(v):
    """Classify by the numeric AQHI value using Health Canada's own bands,
    rather than trusting the AEP feed's HealthRisk field — that field has
    been observed reporting 'Low' for an Aqhi of 4-5 (should be Moderate),
    i.e. it can't be relied on to match its own number."""
    if v is None:
        return 'UNKNOWN'
    if v <= 3:
        return 'LOW'
    if v <= 6:
        return 'MODERATE'
    if v <= 10:
        return 'HIGH'
    return 'EXTREME'

def pm25_to_eaqhi(pm):
    """PM2.5-only estimated-AQHI proxy, same breakpoints as SK_datapull's
    pm25_to_eaqhi — used when official station AQHI is unavailable and we
    fall back to nearby PurpleAir sensors."""
    if pm is None:
        return None
    if pm <= 10:return 1
    if pm <= 20:return 2
    if pm <= 30:return 3
    if pm <= 40:return 4
    if pm <= 50:return 5
    if pm <= 60:return 6
    if pm <= 70:return 7
    if pm <= 80:return 8
    if pm <= 90:return 9
    if pm <= 100:return 10
    return 11
