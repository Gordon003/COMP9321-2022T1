import pandas as pd
from flask import Flask, request
from flask_restx import Resource, Api, fields

# set up api
app = Flask(__name__)
api = Api(app)

# book schema
book_model = api.model('Book', {
    'Flickr_URL': fields.String,
    'Publisher': fields.String,
    'Author': fields.String,
    'Title': fields.String,
    'Date_of_Publication': fields.Integer,
    'Identifier': fields.Integer,
    'Place_of_Publication': fields.String
})

# action on book via its ID
@api.route('/books/<int:id>')
@api.doc(params={'id': 'actor id in sqlitedb'})
class Books(Resource):

    # get book info
    def get(self, id):
        if id not in df.index:
            # api.abort(404, "Book {} doesn't exist".format(id))
            return {"error": "Book does't exist."}, 404

        book = dict(df.loc[id])
        return book

    # delete book
    def delete(self, id):
        if id not in df.index:
            api.abort(404, "Book {} doesn't exist".format(id))

        df.drop(id, inplace=True)
        return {"message": "Book {} is removed.".format(id)}, 200

    # update book
    # @api.expect(book_model)
    def put(self, id):

        if id not in df.index:
            api.abort(404, "Book {} doesn't exist".format(id))

        # get the payload and convert it to a JSON
        book = request.json

        # Book ID cannot be changed
        if 'Identifier' in book and id != book['Identifier']:
            return {"message": "Identifier cannot be changed".format(id)}, 400

        # Update the values
        for key in book:
            if key not in book_model.keys():
                # unexpected column
                return {"message": "Property {} is invalid".format(key)}, 400
            df.loc[id, key] = book[key]

        # df.append(book, ignore_index=True)
        return {"message": "Book {} has been successfully updated".format(id)}, 200

# set up api
if __name__ == '__main__':

    # read dataset into df
    csv_file = "Books.csv"
    df = pd.read_csv(csv_file)

    # drop unnecessary column
    columns_to_drop = ['Edition Statement',
                       'Corporate Author',
                       'Corporate Contributors',
                       'Former owner',
                       'Engraver',
                       'Contributors',
                       'Issuance type',
                       'Shelfmarks'
                       ]
    df.drop(columns_to_drop, inplace=True, axis=1)

    # clean the date of publication & convert it to numeric data
    new_date = df['Date of Publication'].str.extract(r'^(\d{4})', expand=False)
    new_date = pd.to_numeric(new_date)
    new_date = new_date.fillna(0)
    df['Date of Publication'] = new_date

    # replace spaces in the name of columns
    df.columns = [c.replace(' ', '_') for c in df.columns]

    # set index to indentifer
    df.set_index('Identifier', inplace=True)

    # run api
    app.run(debug=True)