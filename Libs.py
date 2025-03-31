import os
import time
import logging
from typing import Generator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_community.retrievers import AmazonKnowledgeBasesRetriever

# Cấu hình logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cấu hình OpenAI
os.environ["OPENAI_API_KEY"] = "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"  # Khuyến nghị dùng biến môi trường

# Cấu hình Knowledge Base
KB_ID = 'CIPIOZMGQZ'

def extract_filename(location_data: dict) -> str:
    """Trích xuất tên file từ metadata AWS"""
    try:
        if isinstance(location_data, dict):
            s3_uri = location_data.get('s3Location', {}).get('uri', '')
            return s3_uri.split('/')[-1] if s3_uri else 'Nguồn không xác định'
        return str(location_data).split('/')[-1]
    except Exception as e:
        logger.error(f"Lỗi trích xuất tên file: {str(e)}")
        return "Nguồn không xác định"

def search_travelwith_fnb(
    prompt: str, 
    chat_history: list = None,
    is_first: bool = False,
    model_name: str = "gpt-4o-2024-08-06"  
) -> Generator[str, None, None]:
    """Xử lý tìm kiếm và streaming response chi tiết"""
    try:
        # Khởi tạo retriever và model
        retriever = AmazonKnowledgeBasesRetriever(
            knowledge_base_id=KB_ID,
            retrieval_config={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                    'overrideSearchType': "SEMANTIC"
                }
            }
        )

        chat = ChatOpenAI(
            model=model_name,  # Sử dụng model được chọn
            temperature=0.1,
            streaming=True
        )

        # Xử lý retrieval documents
        citations = []
        try:
            retrieved_docs = retriever.invoke(prompt)
            for doc in retrieved_docs[:3]:
                source = extract_filename(doc.metadata.get('location', {}))
                content = doc.page_content.split('\n')[0][:150] + "..."
                citations.append({
                    'source': source,
                    'content': content,
                    'full': doc.page_content
                })
        except Exception as e:
            logger.error(f"Lỗi truy vấn dữ liệu: {str(e)}")
            yield "⚠️ Lỗi kết nối hệ thống. Vui lòng thử lại sau."
            return

        # Xây dựng context và system prompt
        context = "\n".join([doc.page_content for doc in retrieved_docs][:3]) if retrieved_docs else ""
        
        system_content = f"""
{'Xin chào, em là chatbot AI tư vấn Edurich' if is_first else ''}
Context: {context[:2000]}

        Bạn là chuyên gia tư vấn các khóa học trên edurich.vn Hãy:
    1. XEM XÉT LỊCH SỬ CHAT TRƯỚC ĐÂY: {chat_history if chat_history else 'Bạn chưa nhắn gì trước đó cả'}
    2. DỰA VÀO CONTEXT HIỆN TẠI: {context}
    3. Trả lời câu hỏi: {prompt}
# Nhân vật
 - Tư vấn viên khóa học Edurich 
# Nhiệm vụ
- Tư vấn các khóa học và combo trên edurich.vn 
# Kinh nghiệm
- 10 năm trong ngành sale 
# Skills
## Skill 1: Giao tiếp
- Luôn trả lời dạ thưa anh/chị nếu chưa biết khách hàng là nam hay nữ. 
- Luôn trả lời  'em' với khách hàng (có thể xưng là 'chúng em' nếu cần), không được trả lời 'chúng tôi'.
- Trả lời lịch sự với khách hàng
## Skill 2: Trả lời theo kịch bản
- Ưu tiên giới thiệu các combo khóa học sau vì nó sẽ rẻ hơn so với các khóa học đơn lẻ:
  + Combo AI toàn diện bao gồm 8 khóa học (Đào tạo ChatGPT chi tiết từ A-Z, Khoá học ChatGPT và AI dành cho người kinh doanh online, Dùng AI xây dựng video marketing, Làm chủ AI - Tổng hợp các AI đỉnh cao, Khai thác tiềm năng ChatGPT - Chìa khoá môi giới bất động sản, Ứng dụng ChatGPT và AI tạo ra thu nhập thụ động, Khám phá bí mật ChatGPT và AI đỉnh cao (Kèm sách), Biên tập video ngắn)
  + Combo AI chuyên gia bao gồm 4 khóa học (Đào tạo ChatGPT chi tiết từ A-Z, Dùng AI xây dựng Video Marketing, Biên tập video ngắn)
  + Combo AI video xây kênh bao gồm 3 khóa học (Đào tạo ChatGPT chi tiết từ A-Z, Dùng AI xây dựng Video Marketing, Biên tập video ngắn: Hướng dẫn bạn biên tập video chuyên nghiệp từ A-Z)
  + Combo Multi Media bao gồm 5 khóa học (Xử lý hình ảnh bằng Photoshop chuyên nghiệp, Thiết kế đồ hoạ 2D chuyên nghiệp với Illustrator, Thiết kế quảng cáo với Corel Draw, Dựng video chuyên nghiệp với Adobe Premiere, Biên tập video ngắn)
  + Combo Phù thuỷ thiết kế bao gồm 3 khóa học (Xử lý hình ảnh bằng Photoshop chuyên nghiệp, Thiết kế đồ hoạ 2D chuyên nghiệp với Illustrator, Thiết kế quảng cáo với Corel Draw)
- Sau khi đã hiểu nhu cầu của khách hàng, liệt kê các khóa học hoặc combo phù hợp với nhu cầu của khách hàng, kèm theo giá và link thanh toán của từng khóa học hoặc combo đó bằng giá và link thanh toán thực tế từ {context}.
- Nếu {context}  không có link, yêu cầu user hỏi lại để cung cấp link chi tiết
- Nêu rõ các lợi ích và giá trị mà khóa học mang lại cho học viên.
- Tự động hỗ trợ tư vấn, chủ động hỏi khách hàng để hiểu về nhu cầu của khách hàng, thuyết phục khách hàng học các khóa học combo. 
- Tự động hỗ trợ tư vấn không để khách chủ động trả lời trước, bot phải chủ động trả lời trước để hiểu được khách hàng cần tìm khóa học hay combo gì để tư vấn, dữ liệu được lấy trong 'course_data_edurich'. 
- Tư vấn và hướng khách hàng tới các khóa học combo (nó bao gồm nhiều các khóa học đơn lẻ) để khách hàng lựa chọn vì các khóa học combo rẻ hơn nhiều so với các khóa đơn lẻ, dữ liệu được lấy trong 'course_data_edurich'. 

"""

        messages = [
            SystemMessage(content=system_content),
            HumanMessage(content=prompt)
        ]

        # Xử lý streaming
        full_response = []
        for chunk in chat.stream(messages):
            content = chunk.content
            if content:
                for char in content:
                    full_response.append(char)
                    yield char
                    time.sleep(0.001)

    except Exception as e:
        logger.error(f"Lỗi tổng hợp: {str(e)}")
        yield "⛔ Đã xảy ra lỗi nghiêm trọng. Vui lòng thử lại sau."