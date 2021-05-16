import pytest
import setup
import app
import pandas as pd
import io

class TestLoadDataFiles:
    def test_load_good_data(self):
        good_data = """,Age,Height,Weight
        0,0,53,3500
        1,6,55,3600
        2,12,59,3700"""
        loaded_data = app.load_datafile(io.StringIO(good_data))
        good_df = pd.read_csv(io.StringIO(good_data))
        print(loaded_data)
        assert loaded_data.equals(good_df)

    def test_load_m_data(self):
        m_data = """,Age,Height,Weight
        0,0,0.53,3500
        1,6,0.55,3600
        2,12,0.59,3700"""
        good_data = """,Age,Height,Weight
        0,0,53,3500
        1,6,55,3600
        2,12,59,3700"""
        loaded_data = app.load_datafile(io.StringIO(m_data))
        good_df = pd.read_csv(io.StringIO(good_data))
        pd.testing.assert_frame_equal(loaded_data, good_df,
            check_dtype=False)

    def test_load_kg_data(self):
        kg_data = """,Age,Height,Weight
        0,0,53,3.5
        1,6,55,3.6
        2,12,59,3.7"""
        good_data = """,Age,Height,Weight
        0,0,53,3500
        1,6,55,3600
        2,12,59,3700"""
        loaded_data = app.load_datafile(io.StringIO(kg_data))
        good_df = pd.read_csv(io.StringIO(good_data))
        pd.testing.assert_frame_equal(loaded_data, good_df,
            check_dtype=False)

    def test_load_sd_data(self):
        kg_data = """,Age,Height,Weight,sd_ht,sd_wt
        0,0,0.53,3.5,0.015,0.05
        1,6,0.55,3.6,0.016,0.08
        2,12,0.59,3.7,0.018,0.1"""
        good_data = """,Age,Height,Weight,sd_ht,sd_wt
        0,0,53,3500,1.5,50
        1,6,55,3600,1.6,80
        2,12,59,3700,1.8,100"""
        loaded_data = app.load_datafile(io.StringIO(kg_data))
        good_df = pd.read_csv(io.StringIO(good_data))
        pd.testing.assert_frame_equal(loaded_data, good_df,
            check_dtype=False)

    def test_wrong_file(self):
        fn = 'completely_stupid_wrong_name.sit'
        assert app.load_datafile(fn) == None