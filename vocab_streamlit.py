#!/usr/bin/env python3
"""
Compatibility entrypoint.

The complete app lives in app.py (banks + mobile UI + daily chain).
Run either:
  streamlit run app.py
  streamlit run vocab_streamlit.py
"""

from app import main

if __name__ == "__main__":
    main()
