export const knowledgeBase = {
  brandName: "晨光烘焙坊",
  businessHours: "週一至週日 09:00 - 18:00（國定假日另行公告）",
  phone: "02-2345-6789",
  email: "service@dawn-bakery.com",
  address: "台北市信義區幸福路 101 號",
  services: [
    "生日蛋糕與客製化蛋糕預訂",
    "麵包、甜點、咖啡與下午茶外帶",
    "DIY 烘焙課程與小型活動包場"
  ],
  faqs: [
    {
      id: "faq-1",
      question: "蛋糕需要提前多久預訂？",
      answer:
        "一般生日蛋糕建議提前 3 天預訂；客製化造型蛋糕建議提前 7 天。若是急件，歡迎直接來電確認當日可製作的款式。"
    },
    {
      id: "faq-2",
      question: "有提供外送服務嗎？",
      answer:
        "目前台北市部分區域可安排外送，滿 2,000 元可免運；未滿 2,000 元會依距離酌收運費。實際可送範圍請提供地址後確認。"
    },
    {
      id: "faq-3",
      question: "可以客製化蛋糕文字或口味嗎？",
      answer:
        "可以。蛋糕文字、尺寸、口味與簡單裝飾都能討論。較複雜的造型或主題設計，建議先留下需求與參考圖片，由專人回覆報價。"
    },
    {
      id: "faq-4",
      question: "店內可以內用嗎？",
      answer:
        "可以，店內座位有限，尖峰時段可能需要候位。若是多人聚會或課程需求，建議提前預約。"
    }
  ]
};

export type KnowledgeBase = typeof knowledgeBase;
