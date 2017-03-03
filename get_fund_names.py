#!/usr/bin/env python3

import pandas
import re


def improve_fund_names(fund_name):
    if not pandas.isnull(fund_name):
        fund_name = re.sub(r":.*$", "", fund_name)
        fund_name = re.sub(r"\(.*\)", "", fund_name)
        fund_name = fund_name.strip()
        return(fund_name)

export = pandas.read_csv("fdbapp_fund_export.csv")
export.columns = ("id", "fund", "fund_manager")

export.fund_improved = export.fund.apply(improve_fund_names)
export.fund_manager_improved = export.fund_manager.apply(improve_fund_names)

funds_and_managers = pandas.Series(list(set(
    export.fund_improved.append(
        export.fund_manager_improved[~export.fund_manager_improved.isnull()]))))

funds_and_managers.to_csv("fund_names.csv")
