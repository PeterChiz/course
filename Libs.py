import os
import boto3
import json
import time
import logging
from typing import Generator
from langchain_community.retrievers import AmazonKnowledgeBasesRetriever

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CLAUDE_SONNET_3_5 = 'anthropic.claude-3-5-sonnet-20240620-v1:0'
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
    is_first: bool = False
) -> Generator[str, None, None]:
    """Xử lý tìm kiếm và streaming response chi tiết"""
    try:
        bedrock = boto3.client(service_name="bedrock-runtime", region_name="us-west-2")
        retriever = AmazonKnowledgeBasesRetriever(
            knowledge_base_id=KB_ID,
            retrieval_config={
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                    'overrideSearchType': "SEMANTIC"
                }
            }
        )

        citations = []
        try:
            retrieved_docs = retriever.invoke(prompt)
            if retrieved_docs:
                for doc in retrieved_docs[:3]:
                    source = extract_filename(doc.metadata.get('location', {}))
                    # Lấy 150 ký tự đầu tiên của từng document và thêm dấu "..."
                    content = doc.page_content.split('\n')[0][:150] + "..."
                    citations.append({'source': source, 'content': content, 'full': doc.page_content})
        except Exception as e:
            logger.error(f"Retrieval error: {str(e)}")
            yield "⚠️ Lỗi kết nối hệ thống. Vui lòng thử lại sau."
            return

        context = "\n".join([doc.page_content for doc in retrieved_docs][:3]) if retrieved_docs else ""
        
        greeting = "Xin chào, em là chatbot AI tư vấn, hỗ trợ anh/chị về khóa học trên nền tảng Edurich.vn.\n\n" if is_first else ""
        system_prompt = f"""{greeting}
{context[:2000]}

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

        response = bedrock.invoke_model_with_response_stream(
            modelId=CLAUDE_SONNET_3_5,
            body=json.dumps({
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 2000,
                "messages": [{"role": "user", "content": system_prompt}],
                "temperature": 0.3
            })
        )

        full_response = []
        for event in response.get('body', []):
            if chunk := event.get('chunk'):
                try:
                    data = json.loads(chunk['bytes'].decode())
                    if text := data.get('delta', {}).get('text', ''):
                        for char in text:
                            full_response.append(char)
                            yield char
                            time.sleep(0.001)
                except Exception as e:
                    logger.error(f"Chunk error: {str(e)}")
                    continue

        answer_text = "".join(full_response)

        # Hàm kiểm tra mức độ liên quan giữa citation và câu trả lời
        def is_relevant(citation_text, answer_text, threshold=0.3):
            cit_words = set(citation_text.lower().split())
            ans_words = set(answer_text.lower().split())
            if not cit_words:
                return False
            ratio = len(cit_words.intersection(ans_words)) / len(cit_words)
            return ratio >= threshold

        # Lọc các citation có liên quan dựa trên citation 'content'
        relevant_citations = [cite for cite in citations if is_relevant(cite['content'], answer_text)]
        
        if relevant_citations:
            # Hiển thị tiêu đề cho phần trích dẫn
            yield "\n\n__📌 Trích dẫn liên quan:__\n"
            for cite in relevant_citations:
                # Nếu cần, bạn có thể rút gọn phần nội dung hiển thị ban đầu
                full_text = cite.get('full', cite['content'])
                truncated = full_text
                if len(full_text) > 300:
                    truncated = full_text[:300] + "..."
                # Tạo toggle sử dụng thẻ <details> và <summary>
                toggle_html = f"""
<details>
  <summary><strong>{cite['source']}</strong> (nhấn để xem chi tiết)</summary>
  <p>{full_text}</p>    
</details>
"""
                yield toggle_html

    except Exception as e:
        logger.error(f"General error: {str(e)}")
        yield "⛔ Đã xảy ra lỗi nghiêm trọng. Vui lòng thử lại sau."
