mock_user = {
    'id': 1,
    'username': 'handmade_lover',
    'nickname': '手作爱好者',
    'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20crafts%20lover%20avatar&image_size=square',
    'phone': '138****8888',
    'email': 'handmade@example.com',
    'gender': 1,
    'role': 'customer',
    'roles': ['customer'],
    'current_role': 'customer',
    'bio': '热爱手作，喜欢制作各种手工制品',
    'create_time': '2024-01-15 10:30:00'
}

mock_users = [
    {
        'id': 1,
        'username': 'handmade_lover',
        'nickname': '手作爱好者',
        'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20crafts%20lover%20avatar&image_size=square',
        'phone': '138****8888',
        'email': 'handmade@example.com',
        'gender': 1,
        'role': 'customer',
        'roles': ['customer'],
        'current_role': 'customer',
        'bio': '热爱手作，喜欢制作各种手工制品',
        'create_time': '2024-01-15 10:30:00'
    },
    {
        'id': 2,
        'username': 'craft_master',
        'nickname': '手作大师',
        'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=craft%20master%20avatar&image_size=square',
        'phone': '139****9999',
        'email': 'craftmaster@example.com',
        'gender': 2,
        'role': 'teacher',
        'roles': ['customer', 'teacher'],
        'current_role': 'teacher',
        'teacher_info': {
            'teacher_id': 'T202306200001',
            'real_name': '李艺',
            'id_card': '110101199001011234',
            'phone': '139****9999',
            'specialties': ['编织', '陶艺', '刺绣'],
            'intro': '资深手作老师，拥有10年手作教学经验',
            'work_photos': [
                'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=handmade%20craft%20workshop%20studio&image_size=square_hd',
                'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=crafts%20display%20showcase&image_size=square_hd'
            ],
            'verified': True,
            'verify_time': '2023-06-20 10:00:00'
        },
        'bio': '资深手作老师，擅长编织、陶艺等多种手作技艺',
        'create_time': '2023-06-20 09:15:00'
    },
    {
        'id': 3,
        'username': 'diy_enthusiast',
        'nickname': 'DIY达人',
        'avatar': 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=diy%20enthusiast%20avatar&image_size=square',
        'phone': '137****7777',
        'email': 'diylover@example.com',
        'gender': 0,
        'role': 'customer',
        'roles': ['customer'],
        'current_role': 'customer',
        'bio': '喜欢尝试各种DIY项目，享受动手创造的乐趣',
        'create_time': '2024-03-10 14:45:00'
    }
]

mock_addresses = [
    {
        'id': 1,
        'user_id': 1,
        'name': '张三',
        'phone': '138****8888',
        'province': '广东省',
        'city': '深圳市',
        'district': '南山区',
        'detail': '科技园南区A栋1001室',
        'is_default': True,
        'create_time': '2024-01-15 10:30:00'
    },
    {
        'id': 2,
        'user_id': 1,
        'name': '李四',
        'phone': '139****9999',
        'province': '广东省',
        'city': '广州市',
        'district': '天河区',
        'detail': '体育西路天河城B座2002室',
        'is_default': False,
        'create_time': '2024-02-20 14:45:00'
    }
]
