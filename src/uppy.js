import Uppy from '@uppy/core'
import Dashboard from '@uppy/dashboard'
import AwsS3 from '@uppy/aws-s3'

import '@uppy/core/dist/style.min.css';
import '@uppy/dashboard/dist/style.min.css';

const uppy = new Uppy({
  debug: true,
})

uppy.use(Dashboard, {
  inline: true,
  target: '#uppy',
})

uppy.use(AwsS3, {
  getUploadParameters (file) {
    return fetch(upload_url, {
      method: 'post',
      headers: {
        accept: 'application/json',
        'content-type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({
        filename: file.name,
        contentType: file.type,
        tripUUID: trip_uuid
      }),
    }).then((response) => {
      return response.json()
    }).then((data) => {
      file.meta['tripUUID'] = trip_uuid;
      return {
        method: data.method,
        url: data.url,
        fields: data.fields,
        headers: data.headers,
      }
    })
  },
})

uppy.on('upload-success', (file, data) => {
    const s3Key = file.meta['key'];
    const tripUUID = file.meta['tripUUID'];
    return fetch(upload_success_url, {
        method: 'post',
        headers: {
            accept: 'application/json',
            'content-type': 'application/json',
            'X-CSRFToken': csrftoken
        },
        body: JSON.stringify({
            s3Key: s3Key,
            tripUUID: tripUUID
        }),
    }).then((response) => {
        return response.json()
    })
});