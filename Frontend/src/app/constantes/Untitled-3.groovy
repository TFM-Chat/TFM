


Revisor BO con el nuevo servicio:


1) AIRLINE_AGREEMENTS_FETCHED

en el BO para ver el resultado del servicio de oak, antes se puede ver el 

2) OUTGOING_HTTP_REQUEST para ver que se le envio



EN NR se puede ver la traza: 

this.insightService.traceCostRuleEvent(NewRelicConstants.OAK_AIRLINE_AGREEMENTS, concept, data, cardData, payment,
   transactionId);

OAK_AIRLINE_AGREEMENTS


Y si hay error en NR: 

tring requestMessage=airlineAgreementsRequestData==null?"":airlineAgreementsRequestData.toString();
String message = String.format(
   "NEW AIRLINE SERVICE AGREEMENTS: Error calling new service with this transaction = %s and this requests = %s and this errorMessage = %s",
   transactionId, requestMessage, e.getMessage());
LOGGER.error("NEW AIRLINE SERVICE AGREEMENTS: general error {}", e.getMessage());
this.monitor.raiseAlert(this.getClass(), message, Collections.emptyMap());
throw e;


3) Para poder ver los cálculos de los comercios luego de ver el snapshot de comercios sera aqui: 

CALC_AIRLINE_AGREEMENTS_IN_COMMERCES



4) Luego de calcular comercios y agregarlo a los gateways de acuedo a las conversiones se puede ver en : 

MAP_AIRLINE_AGREEMENTS_IN_GATEWAYS


5) Luego de obtener los posibles gateway, estos se filtran y el resultado esta en: 

PAYMENT_WITH_AIRLINE_AGREEMENT_OPTIONS

Equivalente pandora->PAYMENT_OPTIONS

6) Verificar los resultados
GATEWAYS_OLD
GATEWAYS_NEW

7) En planes se hace una interseccion y se puede ver en: 

INTERCEPT_AIRLINE_AGREEMENTS_PLAN
 y el equivalente de pandora INTERCEPT_PLAN

8) ADEMAS EN PLANES SE HACE UN FILTRO : INTERCEPT_AIRLINE_AGREEMENTS_PLAN
 Y EN PANDORA EL EQUIVALENTE ES : FILTER_PLAN


—-GRAFANA

Ver errores grouping 

Errores genericos
Ex: ERROR.*paymenttest29
Error solo FARE Ex: paymenttest29.*correct matched grouping.*FLIGHT_FARE

Ver errores planes: 
Errores genericos
ERROR.*testplanskillcombo32

(X-UOW).*NEW AIRLINE SERVICE AGREEMENTS: not manual case.*
ex:
ERROR.*testplanskillcombo32.*NEW AIRLINE SERVICE AGREEMENTS: not manual case.*




—--New relic


