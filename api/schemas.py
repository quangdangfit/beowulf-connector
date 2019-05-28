import coreapi


# purchase_schema = coreapi.Document(
#     title='Business Search API',
#     content={
#         'search': coreapi.Link(
#             url='/api/purchases/',
#             action='get',
#             fields=[
#                 coreapi.Field(
#                     name='account_name',
#                     required=True,
#                     location='query',
#                     description='Search term'
#                 ),
#             ],
#             description='Search business listings'
#         )
#     }
# )