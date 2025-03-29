import streamlit as st
import Libs as glib
import time

st.set_page_config(
    page_title="Edurich",
    page_icon="🌍",
    layout="centered"
)

# Khởi tạo session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
    st.session_state.has_greeted = False

# Hiển thị lời chào ban đầu
if len(st.session_state.messages) == 0 and not st.session_state.has_greeted:
    greeting_text = "Xin chào, em là chatbot AI tư vấn, hỗ trợ anh/chị về khóa học trên nền tảng Edurich.vn"
    with st.chat_message("assistant"):
        def stream_greeting():
            greeting = "Xin chào, em là chatbot AI tư vấn, hỗ trợ anh/chị về khóa học trên nền tảng Edurich.vn"
            for char in greeting:
                yield char
                time.sleep(0.03)
        st.write_stream(stream_greeting())
        st.session_state.messages.append({"role": "assistant", "content": greeting_text})
        st.session_state.has_greeted = True

# Hiển thị lịch sử chat
for msg in st.session_state.messages[1:]:  # Bỏ qua lời chào đầu
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# Xử lý input
if prompt := st.chat_input("Nhập câu hỏi của bạn..."):
    # Thêm câu hỏi vào lịch sử
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt, unsafe_allow_html=True)
    
    with st.chat_message("assistant"):
        response_box = st.empty()
        full_response = []
        
        # Kiểm tra có phải lần đầu tiên không
        is_first = len([m for m in st.session_state.messages if m['role'] == 'user']) == 1
        
        try:
            for chunk in glib.search_travelwith_fnb(
                prompt,
                st.session_state.messages[:-1],
                is_first=is_first
            ):
                full_response.append(chunk)
                current_text = "".join(full_response)
                # Cho phép render HTML (các toggle citation) khi có unsafe_allow_html=True
                response_box.markdown(current_text + "▌", unsafe_allow_html=True)
                time.sleep(0.02)
            
            response_box.markdown(current_text, unsafe_allow_html=True)
            st.session_state.messages.append({"role": "assistant", "content": current_text})
            
        except Exception as e:
            error_msg = "⚠️ Đã xảy ra lỗi. Vui lòng thử lại sau."
            response_box.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})
