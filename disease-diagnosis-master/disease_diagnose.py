import numpy as np
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher

from actions.actions import Action, AdditionalSymptomsAction, GreetingAction, ShowSymsAction, HelpAction, \
    TerminateAction
from actions.handlers import GreetingHandler, AdditionalSymptomsHandler, ShowSymsHandler, TerminateHandler, HelpHandler
from context import Context

from intents.intent_req_handlers import UserInputReqHandler, TerminateReqHandler
from intents.intent_reqs import IntentReq, UserInputIntentReq, TerminateIntentReq
from intents.intents import UserInputIntent, Intent


def process_intent(intent: Intent) -> Action:
    # print('processing intent:', intent)
    ctx: Context = intent.ctx

    if type(intent) == UserInputIntent:
        # check if one of the built in options
        user_input = intent.user_input

        if user_input == 'show symptoms':
            action = ShowSymsAction(ctx)
        elif user_input == 'help':
            action = HelpAction(ctx)
        elif user_input == 'bye' or user_input == 'quit' or user_input == 'exit':
            print('user wants to exit')
            action = TerminateAction(ctx)
        else:
            action = AdditionalSymptomsAction(intent, ctx)
    else:
        raise Exception("unsupported intent type:", type(intent))

    return action


def create_metcher(nlp, symptoms_ds):
    print("creating symptoms matcher")
    sym_series = symptoms_ds['symptom']
    sym_list = sym_series.tolist()
    matcher = PhraseMatcher(nlp.vocab)

    for sym_phrase in sym_list:
        if sym_phrase != '':
            matcher.add('Symptoms', None, nlp(sym_phrase))

    return matcher


def get_input_provider() -> Provider:
        input_provider= Terminal()

        return input_provider


def handle_action(action: Action) -> IntentReq:
    if type(action) == GreetingAction:
        intent_req = GreetingHandler().handle(action)
    elif type(action) == HelpAction:
        intent_req = HelpHandler().handle(action)
    elif type(action) == ShowSymsAction:
        intent_req = ShowSymsHandler().handle(action)
    elif type(action) == AdditionalSymptomsAction:
        intent_req = AdditionalSymptomsHandler().handle(action)
    elif type(action) == TerminateAction:
        intent_req = TerminateHandler().handle(action)
    else:
        raise Exception("no action handler was found for")

    return intent_req


def handle_intent_req(req: IntentReq) -> Intent:
    if type(req) == UserInputIntentReq:
        intent = UserInputReqHandler().handle(req)
    elif type(req) == TerminateIntentReq:
        intent = TerminateReqHandler().handle(req)
    else:
        raise Exception("no action handler was found for")

    return intent


def diagnose(context: Context):
    intent_req = handle_action(GreetingAction(ctx))
    intent = handle_intent_req(intent_req)

    while intent.ctx.in_conversation:
        if intent.ctx.error is not None:
            print("error - ", intent.ctx.error)
            intent.ctx.set_error(None)

        action: Action = process_intent(intent)
        intent = handle_intent_req(handle_action(action))


def init() -> Context:
    nlp = spacy.load('en_core_web_sm')
    # load data sources
    diagnosis_ds = pd.read_csv('sdsort/dia_t.csv')
    symptoms_ds = pd.read_csv('sdsort/sym_t.csv')
    symptoms_ds = symptoms_ds.replace(np.nan, '', regex=True)
    sym_dia_join_table = pd.read_csv('sdsort/diffsydiw.csv')

    sym_dia_ds = symptoms_ds.join(sym_dia_join_table.set_index('syd'), on='syd', how='inner') \
        .join(diagnosis_ds.set_index('did'), on='did', how='inner')

    sym_matcher = create_metcher(nlp, symptoms_ds)

    return Context(nlp, diagnosis_ds, symptoms_ds, sym_dia_ds, sym_matcher)

if __name__ == '__main__':
    ctx = init()
    ctx.set_input_provider(get_input_provider())
    diagnose(ctx)
