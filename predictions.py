#!/usr/bin/env python
# coding: utf-8
import numpy as np
import pandas as pd
from glob import glob
import spacy
import string
import warnings
import fitz
from concurrent import futures
from time import time
from collections import defaultdict
warnings.filterwarnings('ignore')
# pdf_path = "caplaigiaychungnhan/40.pdf"
# Load NER model
model_ner = spacy.load('./model-best/')


# def cleanText(txt):
#     punctuation = "!#$%&\'()*+:;<=>?[\\]^`{|}~-"""
#     tablePunctuation = str.maketrans('', '', punctuation)
#     text = str(txt)
#     removepunctuation = text.translate(tablePunctuation)
#     return str(removepunctuation)
def cleanText(txt):
    punctuation = "!#$%&\'()*+:;<=>?[\\]^`{|}~-"""
    removepunctuation = txt.translate(str.maketrans('', '', punctuation))
    return removepunctuation
# group the label


class groupgen():
    def __init__(self):
        self.id = 0
        self.text = ''

    def getgroup(self, text):
        if self.text == text:
            return self.id
        else:
            self.id += 1
            self.text = text
            return self.id


def parser(text, label):
    if label == 'LOAIGIAY':
        text = text
    elif label == 'COQUANBH':
        text = text
    elif label in ('TENCOSO', 'DIACHISX', 'NGAYBH', 'TRICYEU', 'TGHIEULUC'):
        text = text
        # text = re.sub(r'[^A-Za-z0-9{}]','',text)
    elif label in ('CHUCOSO'):
        text = text
        text.title()
    return text


grp_gen = groupgen()


def process_page(page):
    return page.get_text("text", flags=fitz.TEXT_INHIBIT_SPACES).encode('utf-8').decode('utf-8')


def getPredictions(pdf_path):
    with fitz.open(stream = pdf_path) as doc:
        # with fitz.open(pdf_path) as doc:
        text = ""
        with futures.ThreadPoolExecutor() as executor:
            page_processing = [executor.submit(
                process_page, page) for page in doc]
            for future in futures.as_completed(page_processing):
                text += future.result()
    text = text.strip()
    lines = text.split("\n")
    # Lấy dòng cuối cùng
    last_line = lines[-1]

    # Tách ngày và tháng từ dòng cuối cùng
    date_parts = last_line.split()
    so = lines[-3]

    # Kiểm tra xem dòng cuối cùng có đúng định dạng ngày và tháng hay không
    if len(date_parts) == 2:
        day = date_parts[0]
        month = date_parts[1]

        # Chèn ngày và tháng vào văn bản
        if (day.isdigit() and month.isdigit()):
            text = text.replace("ngày      ", "ngày " + day + " ")
            text = text.replace("Ngày      ", "ngày " + day + " ")
            text = text.replace("tháng    ", "tháng " + month + " ")
        if so.isdigit():
            text = text.replace("Số cấp: ", "Số cấp: " + so)

    text = text.split("\n")[:-2]
    new_text = "\n".join(text)
    # Chia nội dung thành từng dòng
    lines = new_text.splitlines()

    # Xoá các khoảng trắng không cần thiết và kết hợp các dòng lại
    clean_content = ' '.join(line.strip() for line in lines)
    clean_content = cleanText(clean_content)
    doc_new = model_ner(clean_content)
    docjson = doc_new.to_json()
    dataframe_tokens = pd.DataFrame(docjson['tokens'])
    doc_text = docjson['text']
    dataframe_tokens['token'] = dataframe_tokens[['start', 'end']].apply(
        lambda x: doc_text[x[0]:x[1]], axis=1)  # axis = 1 là theo hàng
    # dataframe_tokens['token'] = dataframe_tokens['start'].combine(dataframe_tokens['end'], lambda s, e: doc_text[s:e])
    right_table = pd.DataFrame(docjson['ents'])[
        ['start', 'label']]  # dùng end cx đc
    dataframe_tokens = pd.merge(
        dataframe_tokens, right_table, how='left')
    dataframe_tokens.fillna('O', inplace=True)
    # dataframe_tokens = dataframe_tokens.fillna('O').copy()
    bb_df = dataframe_tokens.query("label != 'O'")
    bb_df['label'] = bb_df['label'].apply(lambda x: x[2:])
    bb_df['group'] = bb_df['label'].apply(grp_gen.getgroup)
    info_arr = dataframe_tokens[['token', 'label']].values
    # entitis = dict(LOAIGIAY=[], COQUANBH=[], TENCOSO=[], DIACHISX=[], NGAYBH=[
    # ], TRICYEU=[], TGHIEULUC=[], CHUCOSO=[], NGUOIKY=[])
    entitis = defaultdict(list)
    previois = 'O'
    for token, label in info_arr:
        bo_tag = label[0]
        label_tag = label[2:]
        text = parser(token, label_tag)
        if bo_tag in ('B', 'I'):
            if previois != label_tag:
                entitis[label_tag].append(text)
            else:
                if bo_tag == "B":
                    entitis[label_tag].append(text)
                else:
                    entitis[label_tag].append(text)
        previois = label_tag
    for key,value in entitis.items():
        join_string = ' '.join(value)
        entitis[key] = join_string

    return entitis

